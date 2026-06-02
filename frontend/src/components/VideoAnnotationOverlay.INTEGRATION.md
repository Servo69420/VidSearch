# VideoAnnotationOverlay — integration notes

`VideoAnnotationOverlay` draws AI-generated shapes (circles, arrows, polygons,
braces, math labels…) on top of the video player. Geometry is rendered in a
16:9 SVG space that matches the player; text/KaTeX labels live in a sibling HTML
layer. Both layers are `position:absolute; inset:0; pointer-events:none`, so the
player still receives clicks.

## Files in this drop
- `VideoAnnotationOverlay.jsx` — the component
- `VideoAnnotationOverlay.css` — its styles (root class `.video-annotation-overlay`)
- `VideoAnnotationOverlay.test.jsx` — vitest + @testing-library/react tests
- `../utils/mathRendering.js` — `looksLikeMathExpression` / `normalizeLatexSource`
  helpers the labels depend on (self-contained, no further imports)

`katex` is already a dependency of this repo, so no package changes are needed.

## Props
```jsx
<VideoAnnotationOverlay annotations={annotations} currentTime={currentTime} />
```
- `annotations` — array of annotation objects, each with `start_s` / `end_s`
  (visibility window) plus its geometry/label fields.
- `currentTime` — current playback time in seconds; the overlay fades each
  annotation in/out around its window.

## Mount point
Render it as a child of the **positioned** element that wraps the player (the
container needs `position: relative` so the overlay's `inset:0` lines up with
the video). In the source app it sits right next to the player element:

```jsx
{/* ...the <video> or YouTube container... */}
<div ref={ytContainerRef} className="video-player" />

{overlaysVisible && (
  <VideoAnnotationOverlay annotations={annotations} currentTime={currentTime} />
)}
```

## Wiring required in WatchPage (not applied — this repo's WatchPage was left untouched)

These are the exact lines from the source app. Adapt names to this repo's player refs.

1. State:
```jsx
const [annotations, setAnnotations] = useState([])
const [currentTime, setCurrentTime] = useState(0)
```

2. A `currentTime` ticker — poll whichever player is active so the overlay knows
   which annotations are visible right now:
```jsx
useEffect(() => {
  let timer = 0
  let stopped = false
  function tick() {
    if (stopped) return
    let t = 0
    if (localVideoUrl) {
      const el = getLocalVideoEl()
      if (el) t = el.currentTime || 0
    } else if (ytReadyRef.current) {
      try { t = ytPlayerRef.current?.getCurrentTime?.() || 0 } catch { /* noop */ }
    }
    setCurrentTime(t)
    timer = window.setTimeout(tick, 100)
  }
  tick()
  return () => { stopped = true; if (timer) clearTimeout(timer) }
}, [activeVideoId, localVideoUrl])
```

3. An annotations data source. In the source app these are persisted per video
   and loaded on mount:
```jsx
fetch(`${API_BASE}/annotations/${encodeURIComponent(activeVideoId)}`, {
  headers: { Authorization: `Bearer ${token}` },
})
  .then(r => (r.ok ? r.json() : []))
  .then(data => { if (Array.isArray(data)) setAnnotations(data) })
```

   > NOTE: this repo has **no `/annotations` backend endpoint yet**, so until one
   > exists `annotations` stays `[]` and the overlay renders nothing. You can
   > feed `annotations` from any source (AI tool calls, local state, a new
   > endpoint) — the component only cares about the array shape and `currentTime`.

That's the whole integration: drop the files in, mount the component over the
player, and supply `annotations` + a ticking `currentTime`.
