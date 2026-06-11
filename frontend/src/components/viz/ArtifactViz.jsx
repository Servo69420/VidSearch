import { useEffect, useRef, useState } from 'react'

// Renders an LLM-generated, self-contained HTML document as an interactive
// "artifact" inside a sandboxed iframe.
//
// SECURITY: sandbox="allow-scripts" WITHOUT allow-same-origin → the frame runs
// in a unique opaque origin and cannot read the parent DOM, cookies, or
// localStorage. A strict CSP injected into the document blocks all network
// egress, so the artifact cannot exfiltrate data or load external code.
const CSP =
  "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; " +
  "img-src data:; font-src data:;"

// Injected into the artifact so it reports its content height for auto-resize.
const BOOTSTRAP = `
<script>
  (function () {
    var lastHeight = 0;
    function measure() {
      // Layout height, not scrollHeight: hover transforms (scale/translate)
      // extend scrollable overflow without changing layout, and measuring
      // them caused a hover -> resize -> re-hover jitter loop. Only trust
      // scrollHeight when it dwarfs the layout height (100vh-style documents
      // whose real content overflows), never for few-px hover overflow.
      var doc = document.documentElement;
      var body = document.body;
      var layout = Math.max(doc ? doc.offsetHeight : 0, body ? body.offsetHeight : 0);
      var scroll = Math.max(doc ? doc.scrollHeight : 0, body ? body.scrollHeight : 0);
      return scroll > layout + 48 ? scroll : layout;
    }
    function postHeight() {
      var h = measure();
      // Resizing the iframe changes its viewport, which fires resize/observer
      // again — the threshold breaks that feedback loop so the frame doesn't
      // jitter or creep up to the height cap (vh-based layouts especially).
      if (Math.abs(h - lastHeight) < 8) return;
      lastHeight = h;
      parent.postMessage({ type: 'vidviz-height', height: h }, '*');
    }
    window.addEventListener('load', postHeight);
    window.addEventListener('resize', postHeight);
    try { new ResizeObserver(postHeight).observe(document.documentElement); } catch (e) {}
    setTimeout(postHeight, 50);
  })();
</script>`

function wrapHtml(html) {
  const meta = `<meta http-equiv="Content-Security-Policy" content="${CSP}">`
  // Full document → inject CSP into <head>; fragment → build a minimal doc.
  if (/<html[\s>]/i.test(html)) {
    if (/<head[\s>]/i.test(html)) {
      return html.replace(/<head([\s>])/i, `<head$1${meta}`) + BOOTSTRAP
    }
    return html.replace(/<html([\s>])/i, `<html$1<head>${meta}</head>`) + BOOTSTRAP
  }
  return `<!doctype html><html><head>${meta}<style>body{margin:0;font-family:system-ui,sans-serif;}</style></head><body>${html}${BOOTSTRAP}</body></html>`
}

// The sandboxed frame for one artifact version. Height auto-resize and the
// "building" placeholder are per-document state, so the parent remounts this
// (via key) whenever another version is shown — fresh state, no resets.
function ArtifactFrame({ html, title, onTimestampClick }) {
  const iframeRef = useRef(null)
  const [height, setHeight] = useState(160)
  const [loaded, setLoaded] = useState(false)
  const heightRef = useRef(160)
  const shrinkTimerRef = useRef(null)

  useEffect(() => {
    // Grow immediately, shrink only after the smaller height has been stable
    // for a moment. In-flow hover effects (tooltips, expanding panels)
    // otherwise oscillate: the shrink shifts content under the cursor, which
    // re-hovers and grows it again.
    function applyHeight(reported) {
      // The cap only guards against runaway vh-feedback growth — the frame
      // expands to the full document height (the chat panel scrolls).
      const next = Math.min(4000, Math.max(80, reported))
      clearTimeout(shrinkTimerRef.current)
      if (next >= heightRef.current) {
        heightRef.current = next
        setHeight(next)
      } else {
        shrinkTimerRef.current = setTimeout(() => {
          heightRef.current = next
          setHeight(next)
        }, 500)
      }
    }

    function onMessage(e) {
      if (e.source !== iframeRef.current?.contentWindow) return
      const msg = e.data
      if (!msg || typeof msg !== 'object') return
      if (msg.type === 'vidviz-height' && typeof msg.height === 'number') {
        applyHeight(msg.height)
        setLoaded(true)
      } else if (msg.type === 'vidviz-seek' && typeof msg.seconds === 'number') {
        onTimestampClick?.(msg.seconds)
      }
    }
    window.addEventListener('message', onMessage)
    return () => {
      window.removeEventListener('message', onMessage)
      clearTimeout(shrinkTimerRef.current)
    }
  }, [onTimestampClick])

  // Safety net: if the artifact never reports a height (its script crashed
  // before the bootstrap ran), drop the placeholder rather than show it forever.
  useEffect(() => {
    const timer = setTimeout(() => setLoaded(true), 4000)
    return () => clearTimeout(timer)
  }, [])

  return (
    <div className="vidviz-artifact-body">
      {!loaded && (
        <div className="vidviz-artifact-loading">
          <span className="vidviz-artifact-spinner" />
          Building visualization…
        </div>
      )}
      <iframe
        ref={iframeRef}
        className="vidviz-artifact-frame"
        sandbox="allow-scripts"
        srcDoc={wrapHtml(html)}
        title={title}
        style={{ height: `${height}px` }}
      />
    </div>
  )
}

function ArtifactViz({ data, onTimestampClick, onRegenerate }) {
  // A regenerated artifact carries its older versions (data.versions, oldest
  // first); a freshly generated one is a bare version dict. When a
  // regeneration adds a version, VizBlock changes this component's key, so a
  // fresh mount picks up the spec's active index — no state syncing needed.
  const versions = Array.isArray(data?.versions) && data.versions.length
    ? data.versions
    : (data ? [data] : [])
  const lastIndex = versions.length - 1
  const specActive = typeof data?.active === 'number'
    ? Math.min(Math.max(data.active, 0), lastIndex)
    : lastIndex
  const [active, setActive] = useState(specActive)

  const shown = Math.min(Math.max(active, 0), lastIndex)
  const current = versions[shown]
  const html = typeof current?.html === 'string' ? current.html : ''
  const description = typeof current?.description === 'string' ? current.description : ''
  const title = current?.title || 'Visualization'

  if (!html) return null

  return (
    <div className="vidviz-artifact">
      <div className="vidviz-artifact-header">
        <span className="vidviz-artifact-title">{title}</span>
        <span className="vidviz-artifact-actions">
          {versions.length > 1 && (
            <span className="vidviz-version-nav">
              <button
                className="vidviz-version-btn"
                type="button"
                onClick={() => setActive(a => Math.max(0, a - 1))}
                disabled={shown <= 0}
                aria-label="Previous version"
              >
                ‹
              </button>
              <span className="vidviz-version-count">
                {shown + 1}/{versions.length}
              </span>
              <button
                className="vidviz-version-btn"
                type="button"
                onClick={() => setActive(a => Math.min(lastIndex, a + 1))}
                disabled={shown >= lastIndex}
                aria-label="Next version"
              >
                ›
              </button>
            </span>
          )}
          {onRegenerate && description && (
            <button
              className="vidviz-regen-btn"
              type="button"
              onClick={() => onRegenerate(description)}
              title="Generate this visualization again"
            >
              ↻ Regenerate
            </button>
          )}
        </span>
      </div>
      <ArtifactFrame
        key={shown}
        html={html}
        title={title}
        onTimestampClick={onTimestampClick}
      />
    </div>
  )
}

export default ArtifactViz
