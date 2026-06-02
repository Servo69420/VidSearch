import { memo, useEffect, useMemo, useRef, useState } from 'react'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import './VideoAnnotationOverlay.css'
import { looksLikeMathExpression, normalizeLatexSource } from '../utils/mathRendering'

function renderLatex(src) {
  try {
    return katex.renderToString(normalizeLatexSource(src), { throwOnError: false, displayMode: false })
  } catch {
    return src
  }
}

// Two-layer overlay placed inside .video-frame, on top of the YouTube iframe
// or local <video>. Geometry (circles, arrows, polygons, braces…) is drawn in
// a 16:9 SVG space matching the player. Text labels live in a sibling HTML
// layer so they get real CSS typography and clean KaTeX rendering instead of
// fighting <text>/<foreignObject>. Both layers share the same inset:0 box and
// pointer-events:none so the player still receives clicks.

const DEFAULT_COLOR = '#ff3b3b'
const SVG_W = 16
const SVG_H = 9
const DEFAULT_STROKE = 0.064
const DEFAULT_FADE_S = 0.4
// Default marker ring radius (fraction of SVG height). Sized to wrap a
// single character on a typical math board without dominating the frame.
const DEFAULT_MARKER_R = 0.025

function isVisibleAt(ann, t) {
  return t >= ann.start_s && t <= ann.end_s
}

function opacityFor(ann, t) {
  if (t < ann.start_s || t > ann.end_s) return 0
  const fadeIn = Math.min(1, (t - ann.start_s) / DEFAULT_FADE_S)
  const fadeOut = Math.min(1, (ann.end_s - t) / DEFAULT_FADE_S)
  return Math.max(0, Math.min(fadeIn, fadeOut))
}

function sx(x) {
  return x * SVG_W
}

function sy(y) {
  return y * SVG_H
}

function sr(r) {
  return r * SVG_H
}

function sp(point) {
  if (!Array.isArray(point)) return []
  const [x, y] = point
  return [sx(x), sy(y)]
}

function pointsAttr(points) {
  return points.map(([x, y]) => `${sx(x)},${sy(y)}`).join(' ')
}

// Build a curly-brace SVG path from (fx,fy) to (tx,ty). `side` controls which
// way the apex points (perpendicular to the from→to vector).
function bracePath(from, to, side = 'top') {
  if (!Array.isArray(from) || !Array.isArray(to)) return ''
  const [fx, fy] = from
  const [tx, ty] = to
  const mx = (fx + tx) / 2
  const my = (fy + ty) / 2
  const dx = tx - fx
  const dy = ty - fy
  const len = Math.hypot(dx, dy) || 1
  let px = dy / len
  let py = -dx / len
  if (side === 'bottom' || side === 'right') { px = -px; py = -py }
  const depth = Math.min(0.03, len * 0.15)
  const c1x = fx + px * depth, c1y = fy + py * depth
  const m1x = mx + px * depth, m1y = my + py * depth
  const ax = mx + px * depth * 2, ay = my + py * depth * 2
  const c2x = tx + px * depth, c2y = ty + py * depth
  return `M ${fx} ${fy} C ${c1x} ${c1y}, ${m1x} ${m1y}, ${ax} ${ay} ` +
         `C ${m1x} ${m1y}, ${c2x} ${c2y}, ${tx} ${ty}`
}

// Endpoint-form ellipse renders here, not in SVG: the SVG viewBox uses
// preserveAspectRatio="none" so an SVG rotation doesn't match the visual
// angle unless the player is exactly 16:9. CSS rotation is in screen
// pixels, so the math just works.
function OvalHtml({ ann, containerSize, opacity }) {
  const { from, to, thickness } = ann.payload
  const [fx, fy] = from
  const [tx, ty] = to
  const { w: cw, h: ch } = containerSize
  const dxPx = (tx - fx) * cw
  const dyPx = (ty - fy) * ch
  const lengthPx = Math.hypot(dxPx, dyPx)
  const angleDeg = (Math.atan2(dyPx, dxPx) * 180) / Math.PI
  // Pad so the oval extends past the endpoints by half its thickness —
  // matches how a hand-drawn ellipse wraps a line segment.
  const thicknessPx = Math.max(2, (thickness || 0.04) * ch)
  const widthPx = lengthPx + thicknessPx
  const cxPct = ((fx + tx) / 2) * 100
  const cyPct = ((fy + ty) / 2) * 100
  const color = ann.style?.color || DEFAULT_COLOR
  return (
    <div
      className="vao-oval"
      style={{
        left: `${cxPct}%`,
        top: `${cyPct}%`,
        width: `${widthPx}px`,
        height: `${thicknessPx}px`,
        borderColor: color,
        transform: `translate(-50%, -50%) rotate(${angleDeg}deg)`,
        opacity,
      }}
    />
  )
}

function HtmlLabel({ text, x, y, color, latex, opacity, align = 'left' }) {
  if (!text) return null
  const renderAsLatex = latex || looksLikeMathExpression(text)
  // align='right' means the anchor (x,y) is the RIGHT edge of the label,
  // i.e. the label extends to the LEFT of x. We use this to flip labels
  // away from the right edge of the frame so they don't clip out of view.
  const className =
    `vao-label${renderAsLatex ? ' vao-label-latex' : ''}` +
    (align === 'right' ? ' vao-label-right' : '')
  const style = { left: `${x * 100}%`, top: `${y * 100}%`, color, opacity }
  if (renderAsLatex) {
    return (
      <span
        className={className}
        style={style}
        // KaTeX output is trusted: throwOnError:false; KaTeX itself sanitises.
        dangerouslySetInnerHTML={{ __html: renderLatex(text) }}
      />
    )
  }
  return <span className={className} style={style}>{text}</span>
}

// Pick label anchor side based on how close to the frame edges it would
// be. `right` is the natural-side anchor (label extends rightward);
// `left` is the mirror anchor (label extends leftward). Same logic for
// top/bottom: anchors close to the top edge get flipped below the shape.
const LABEL_EDGE_RIGHT = 0.82
const LABEL_EDGE_TOP = 0.04

function pickAnchor({ rightX, leftX, aboveY, belowY, text, latex }) {
  let x = rightX
  let align = 'left'
  if (rightX != null && rightX > LABEL_EDGE_RIGHT && leftX != null) {
    x = leftX
    align = 'right'
  } else if (rightX == null && leftX != null) {
    x = leftX
    align = 'right'
  }
  let y = aboveY
  if (aboveY != null && aboveY < LABEL_EDGE_TOP && belowY != null) {
    y = belowY
  } else if (aboveY == null && belowY != null) {
    y = belowY
  }
  return { x, y, text, latex, align }
}

// Where the label anchors for a given annotation kind. Mirrors the offsets
// that were previously inlined in each Shape branch.
function labelAnchorFor(ann) {
  const label = ann.style?.label
  const latex = !!ann.style?.label_latex
  if (!label && ann.kind !== 'text') return null
  switch (ann.kind) {
    case 'marker': {
      const { x, y } = ann.payload
      if (x == null || y == null) return null
      return pickAnchor({
        rightX: x + DEFAULT_MARKER_R + 0.01,
        leftX:  x - DEFAULT_MARKER_R - 0.01,
        aboveY: y, belowY: y,
        text: label, latex,
      })
    }
    case 'circle': {
      const { cx, cy, r } = ann.payload
      return pickAnchor({
        rightX: cx + r + 0.01,
        leftX:  cx - r - 0.01,
        aboveY: cy, belowY: cy,
        text: label, latex,
      })
    }
    case 'ellipse': {
      if (ann.payload.from && ann.payload.to) {
        const [fx, fy] = ann.payload.from
        const [tx, ty] = ann.payload.to
        const mx = (fx + tx) / 2
        const my = (fy + ty) / 2
        return pickAnchor({
          rightX: mx, leftX: mx,
          aboveY: my - 0.04, belowY: my + 0.04,
          text: label, latex,
        })
      }
      const { cx, cy, rx, ry } = ann.payload
      return pickAnchor({
        rightX: cx + (rx || 0) + 0.01,
        leftX:  cx - (rx || 0) - 0.01,
        aboveY: cy, belowY: cy + (ry || 0) + 0.03,
        text: label, latex,
      })
    }
    case 'rect': {
      const { x, y, w, h } = ann.payload
      return pickAnchor({
        rightX: x, leftX: x + (w || 0),
        aboveY: y - 0.01, belowY: y + (h || 0) + 0.03,
        text: label, latex,
      })
    }
    case 'line': {
      const [fx, fy] = ann.payload.from || []
      const [tx, ty] = ann.payload.to || []
      if (fx == null || tx == null) return null
      const mx = (fx + tx) / 2
      const my = (fy + ty) / 2
      return pickAnchor({
        rightX: mx, leftX: mx,
        aboveY: my - 0.01, belowY: my + 0.03,
        text: label, latex,
      })
    }
    case 'brace': {
      const { from, to } = ann.payload
      if (!Array.isArray(from) || !Array.isArray(to)) return null
      const mx = (from[0] + to[0]) / 2
      const my = (from[1] + to[1]) / 2
      return pickAnchor({
        rightX: mx, leftX: mx,
        aboveY: my - 0.04, belowY: my + 0.04,
        text: label, latex,
      })
    }
    case 'polygon': {
      const p0 = ann.payload.points?.[0]
      if (!p0) return null
      return pickAnchor({
        rightX: p0[0], leftX: p0[0],
        aboveY: p0[1] - 0.01, belowY: p0[1] + 0.03,
        text: label, latex,
      })
    }
    case 'arrow': {
      const [fx, fy] = ann.payload.from || []
      const [tx, ty] = ann.payload.to || []
      if (fx == null || tx == null) return null
      const mx = (fx + tx) / 2
      const my = (fy + ty) / 2
      return pickAnchor({
        rightX: mx, leftX: mx,
        aboveY: my - 0.01, belowY: my + 0.03,
        text: label, latex,
      })
    }
    case 'text': {
      const { x, y, text, latex: textLatex } = ann.payload
      // draw_text is an explicit anchor — don't try to flip; the model
      // already picked the point.
      return { x, y, text, latex: textLatex, align: 'left' }
    }
    default:
      return null
  }
}

function ShapeGeometry({ ann }) {
  const color = ann.style?.color || DEFAULT_COLOR
  const stroke = DEFAULT_STROKE

  switch (ann.kind) {
    case 'marker': {
      const { x, y } = ann.payload
      if (x == null || y == null) return null
      const r = sr(DEFAULT_MARKER_R)
      return (
        <circle
          cx={sx(x)} cy={sy(y)} r={r}
          fill="none" stroke={color} strokeWidth={stroke}
        />
      )
    }
    case 'circle': {
      const { cx, cy, r } = ann.payload
      return <circle cx={sx(cx)} cy={sy(cy)} r={sr(r)} fill="none" stroke={color} strokeWidth={stroke} />
    }
    case 'ellipse': {
      // Endpoint form renders in the HTML layer (see OvalHtml) so the
      // rotation is computed in screen space and isn't distorted by the
      // SVG's preserveAspectRatio="none". Skip it here.
      if (ann.payload.from && ann.payload.to) return null
      const { cx, cy, rx, ry, rotation_deg } = ann.payload
      const rot = rotation_deg || 0
      const rcx = sx(cx)
      const rcy = sy(cy)
      return (
        <ellipse
          cx={rcx} cy={rcy} rx={sx(rx)} ry={sy(ry)}
          fill="none" stroke={color} strokeWidth={stroke}
          transform={`rotate(${rot} ${rcx} ${rcy})`}
        />
      )
    }
    case 'rect': {
      const { x, y, w, h } = ann.payload
      return <rect x={sx(x)} y={sy(y)} width={sx(w)} height={sy(h)} fill="none" stroke={color} strokeWidth={stroke} />
    }
    case 'line': {
      const [fx, fy] = ann.payload.from || []
      const [tx, ty] = ann.payload.to || []
      if (fx == null || tx == null) return null
      return <line x1={sx(fx)} y1={sy(fy)} x2={sx(tx)} y2={sy(ty)} stroke={color} strokeWidth={stroke} />
    }
    case 'brace': {
      const { from, to, side } = ann.payload
      const d = bracePath(sp(from), sp(to), side)
      if (!d) return null
      return <path d={d} fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round" />
    }
    case 'polygon': {
      return (
        <polygon
          points={pointsAttr(ann.payload.points || [])}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinejoin="round"
        />
      )
    }
    case 'arrow': {
      const [fx, fy] = ann.payload.from
      const [tx, ty] = ann.payload.to
      return <line x1={sx(fx)} y1={sy(fy)} x2={sx(tx)} y2={sy(ty)} stroke={color} strokeWidth={stroke} markerEnd="url(#vao-arrow)" />
    }
    case 'text':
    default:
      return null
  }
}

const VideoAnnotationOverlay = memo(function VideoAnnotationOverlay({
  annotations,
  currentTime,
}) {
  const t = currentTime ?? 0
  const visible = useMemo(
    () => (annotations || []).filter(a => isVisibleAt(a, t)),
    [annotations, t]
  )
  const rootRef = useRef(null)
  const [containerSize, setContainerSize] = useState({ w: 0, h: 0 })
  useEffect(() => {
    const el = rootRef.current
    if (!el || typeof ResizeObserver === 'undefined') return undefined
    const ro = new ResizeObserver(entries => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect
        setContainerSize({ w: width, h: height })
      }
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  if (!visible.length) return null

  return (
    <div className="video-annotation-overlay" aria-hidden ref={rootRef}>
      <svg
        className="vao-svg-layer"
        viewBox={`0 0 ${SVG_W} ${SVG_H}`}
        preserveAspectRatio="none"
      >
        <defs>
          <marker
            id="vao-arrow"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M0,0 L10,5 L0,10 z" fill="currentColor" />
          </marker>
        </defs>
        {visible.map(ann => (
          <g
            key={ann.id}
            style={{ opacity: opacityFor(ann, t), color: ann.style?.color || DEFAULT_COLOR }}
          >
            <ShapeGeometry ann={ann} />
          </g>
        ))}
      </svg>
      <div className="vao-html-layer">
        {visible.map(ann => {
          if (ann.kind === 'ellipse' && ann.payload.from && ann.payload.to) {
            return (
              <OvalHtml
                key={`oval-${ann.id}`}
                ann={ann}
                containerSize={containerSize}
                opacity={opacityFor(ann, t)}
              />
            )
          }
          return null
        })}
        {visible.map(ann => {
          const a = labelAnchorFor(ann)
          if (!a) return null
          return (
            <HtmlLabel
              key={ann.id}
              text={a.text}
              x={a.x}
              y={a.y}
              color={ann.style?.color || DEFAULT_COLOR}
              latex={a.latex}
              align={a.align}
              opacity={opacityFor(ann, t)}
            />
          )
        })}
      </div>
    </div>
  )
})

export default VideoAnnotationOverlay
