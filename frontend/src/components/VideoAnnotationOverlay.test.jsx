import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import VideoAnnotationOverlay from './VideoAnnotationOverlay'

function ann(overrides = {}) {
  return {
    id: 'a1',
    kind: 'circle',
    payload: { cx: 0.5, cy: 0.5, r: 0.1 },
    start_s: 1,
    end_s: 5,
    style: { color: '#ff0000' },
    confidence: 0.9,
    ...overrides,
  }
}

describe('VideoAnnotationOverlay', () => {
  it('renders nothing when annotations is empty', () => {
    const { container } = render(<VideoAnnotationOverlay annotations={[]} currentTime={0} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders nothing before start_s', () => {
    const { container } = render(<VideoAnnotationOverlay annotations={[ann()]} currentTime={0} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders nothing after end_s', () => {
    const { container } = render(<VideoAnnotationOverlay annotations={[ann()]} currentTime={10} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders a circle when currentTime is inside the window', () => {
    const { container } = render(<VideoAnnotationOverlay annotations={[ann()]} currentTime={3} />)
    const root = container.querySelector('.video-annotation-overlay')
    expect(root).not.toBeNull()
    const svg = root.querySelector('svg.vao-svg-layer')
    expect(svg).not.toBeNull()
    expect(svg.getAttribute('viewBox')).toBe('0 0 16 9')
    expect(svg.getAttribute('preserveAspectRatio')).toBe('none')
    expect(root.querySelector('.vao-html-layer')).not.toBeNull()
    const circle = svg.querySelector('circle')
    expect(circle).not.toBeNull()
    expect(circle.getAttribute('cx')).toBe('8')
    expect(circle.getAttribute('cy')).toBe('4.5')
    expect(circle.getAttribute('r')).toBe('0.9')
  })

  it('renders an ellipse in the 16:9 video coordinate space while preserving rotation', () => {
    const a = ann({
      id: 'e1',
      kind: 'ellipse',
      payload: { cx: 0.5, cy: 0.5, rx: 0.2, ry: 0.05, rotation_deg: 32 },
    })
    const { container } = render(<VideoAnnotationOverlay annotations={[a]} currentTime={3} />)
    const ellipse = container.querySelector('ellipse')
    expect(ellipse).not.toBeNull()
    expect(ellipse.getAttribute('cx')).toBe('8')
    expect(ellipse.getAttribute('cy')).toBe('4.5')
    expect(ellipse.getAttribute('rx')).toBe('3.2')
    expect(ellipse.getAttribute('ry')).toBe('0.45')
    expect(ellipse.getAttribute('transform')).toBe('rotate(32 8 4.5)')
  })

  it('flips a label to the left side when the shape sits near the right edge', () => {
    const a = ann({
      id: 'edge1',
      kind: 'circle',
      payload: { cx: 0.95, cy: 0.5, r: 0.03 },
      style: { color: '#ff0000', label: 'AB' },
    })
    const { container } = render(<VideoAnnotationOverlay annotations={[a]} currentTime={3} />)
    const label = container.querySelector('.vao-html-layer .vao-label')
    expect(label).not.toBeNull()
    expect(label.classList.contains('vao-label-right')).toBe(true)
    // Anchor moved to the LEFT of the shape (cx - r - 0.01 = 0.91).
    expect(parseFloat(label.style.left)).toBeLessThan(95)
  })

  it('keeps a label on the right side when the shape is in the centre', () => {
    const a = ann({
      id: 'edge2',
      kind: 'circle',
      payload: { cx: 0.4, cy: 0.5, r: 0.05 },
      style: { color: '#ff0000', label: 'AB' },
    })
    const { container } = render(<VideoAnnotationOverlay annotations={[a]} currentTime={3} />)
    const label = container.querySelector('.vao-html-layer .vao-label')
    expect(label).not.toBeNull()
    expect(label.classList.contains('vao-label-right')).toBe(false)
  })

  it('renders a marker as a small SVG circle at the target point', () => {
    const a = ann({
      id: 'm1',
      kind: 'marker',
      payload: { x: 0.25, y: 0.4 },
    })
    const { container } = render(<VideoAnnotationOverlay annotations={[a]} currentTime={3} />)
    const circle = container.querySelector('svg.vao-svg-layer circle')
    expect(circle).not.toBeNull()
    expect(circle.getAttribute('cx')).toBe('4')
    expect(circle.getAttribute('cy')).toBe('3.6')
    expect(circle.getAttribute('fill')).toBe('none')
  })

  it('endpoint-form ellipse renders in HTML layer, not SVG', () => {
    const a = ann({
      id: 'eo1',
      kind: 'ellipse',
      payload: { from: [0.1, 0.2], to: [0.6, 0.4], thickness: 0.05 },
    })
    const { container } = render(<VideoAnnotationOverlay annotations={[a]} currentTime={3} />)
    expect(container.querySelector('svg ellipse')).toBeNull()
    const oval = container.querySelector('.vao-html-layer .vao-oval')
    expect(oval).not.toBeNull()
    expect(oval.style.left).toMatch(/^35(\.0+)?%$/)
    expect(oval.style.top).toMatch(/^30(\.0+\d*)?%$/)
    expect(oval.style.transform).toMatch(/rotate\(/)
  })

  it('renders a polygon with the right point count', () => {
    const a = ann({
      id: 'p1',
      kind: 'polygon',
      payload: { points: [[0.1, 0.1], [0.5, 0.1], [0.3, 0.4]] },
    })
    const { container } = render(<VideoAnnotationOverlay annotations={[a]} currentTime={3} />)
    const poly = container.querySelector('polygon')
    expect(poly).not.toBeNull()
    expect(poly.getAttribute('points').split(' ')).toHaveLength(3)
  })

  it('renders an arrow line + arrowhead marker', () => {
    const a = ann({
      id: 'ar1',
      kind: 'arrow',
      payload: { from: [0.1, 0.2], to: [0.8, 0.7] },
    })
    const { container } = render(<VideoAnnotationOverlay annotations={[a]} currentTime={3} />)
    const line = container.querySelector('line')
    expect(line).not.toBeNull()
    expect(line.getAttribute('marker-end')).toBe('url(#vao-arrow)')
    expect(line.getAttribute('x1')).toBe('1.6')
    expect(line.getAttribute('y1')).toBe('1.8')
    expect(line.getAttribute('x2')).toBe('12.8')
    expect(line.getAttribute('y2')).toBe('6.3')
    expect(container.querySelector('marker#vao-arrow')).not.toBeNull()
  })

  it('renders a plain text label as an HTML span', () => {
    const a = ann({
      id: 't1',
      kind: 'text',
      payload: { x: 0.3, y: 0.4, text: 'hello', latex: false },
    })
    const { container } = render(<VideoAnnotationOverlay annotations={[a]} currentTime={3} />)
    const label = container.querySelector('.vao-html-layer .vao-label')
    expect(label).not.toBeNull()
    expect(label.textContent).toBe('hello')
    expect(label.style.left).toBe('30%')
    expect(label.style.top).toBe('40%')
    expect(container.querySelector('foreignObject')).toBeNull()
  })

  it('renders a LaTeX label as an HTML span containing KaTeX output', () => {
    const a = ann({
      id: 't2',
      kind: 'text',
      payload: { x: 0.3, y: 0.4, text: 'x^2', latex: true },
    })
    const { container } = render(<VideoAnnotationOverlay annotations={[a]} currentTime={3} />)
    const label = container.querySelector('.vao-html-layer .vao-label-latex')
    expect(label).not.toBeNull()
    expect(label.querySelector('.katex')).not.toBeNull()
    expect(container.querySelector('foreignObject')).toBeNull()
  })

  it('renders a shape label as KaTeX when style.label_latex is set', () => {
    const a = ann({
      id: 'cl',
      kind: 'circle',
      payload: { cx: 0.5, cy: 0.5, r: 0.1 },
      style: { color: '#ff0000', label: 'x^2', label_latex: true },
    })
    const { container } = render(<VideoAnnotationOverlay annotations={[a]} currentTime={3} />)
    const label = container.querySelector('.vao-html-layer .vao-label-latex')
    expect(label).not.toBeNull()
    expect(label.querySelector('.katex')).not.toBeNull()
  })

  it('renders a shape label as plain text when label_latex is not set', () => {
    const a = ann({
      id: 'cl2',
      kind: 'circle',
      payload: { cx: 0.5, cy: 0.5, r: 0.1 },
      style: { color: '#ff0000', label: 'hi' },
    })
    const { container } = render(<VideoAnnotationOverlay annotations={[a]} currentTime={3} />)
    const label = container.querySelector('.vao-html-layer .vao-label')
    expect(label).not.toBeNull()
    expect(label.textContent).toBe('hi')
    expect(container.querySelector('.vao-label-latex')).toBeNull()
  })

  it('auto-renders LaTeX-looking overlay text even when the latex flag is missing', () => {
    const a = ann({
      id: 't3',
      kind: 'text',
      payload: { x: 0.3, y: 0.4, text: '90^\\circ', latex: false },
    })
    const { container } = render(<VideoAnnotationOverlay annotations={[a]} currentTime={3} />)
    const label = container.querySelector('.vao-html-layer .vao-label-latex')
    expect(label).not.toBeNull()
    expect(label.querySelector('.katex')).not.toBeNull()
    expect(label.querySelector('.katex-html').textContent).toContain('∘')
  })

  it('shows only the annotations whose window contains currentTime', () => {
    const a = ann({ id: 'visible' })
    const b = ann({ id: 'past', start_s: 100, end_s: 200 })
    const { container } = render(<VideoAnnotationOverlay annotations={[a, b]} currentTime={3} />)
    expect(container.querySelectorAll('circle')).toHaveLength(1)
  })
})
