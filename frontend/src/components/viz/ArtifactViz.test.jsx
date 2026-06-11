import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ArtifactViz from './ArtifactViz'
import { VizBlock } from './registry'

const version = (n) => ({
  title: `Viz ${n}`,
  description: `desc ${n}`,
  html: `<p>v${n}</p>`,
})

describe('ArtifactViz version switching', () => {
  it('renders no arrows for a single bare version', () => {
    render(<ArtifactViz data={version(1)} />)
    expect(screen.queryByLabelText('Previous version')).toBeNull()
    expect(screen.queryByLabelText('Next version')).toBeNull()
  })

  it('shows the active version and the counter', () => {
    render(<ArtifactViz data={{ versions: [version(1), version(2)], active: 1 }} />)
    expect(screen.getByText('2/2')).not.toBeNull()
    expect(screen.getByText('Viz 2')).not.toBeNull()
  })

  it('arrows switch between versions and clamp at the ends', () => {
    render(<ArtifactViz data={{ versions: [version(1), version(2)], active: 1 }} />)
    const prev = screen.getByLabelText('Previous version')
    const next = screen.getByLabelText('Next version')

    expect(next.disabled).toBe(true)
    fireEvent.click(prev)
    expect(screen.getByText('1/2')).not.toBeNull()
    expect(screen.getByText('Viz 1')).not.toBeNull()
    expect(prev.disabled).toBe(true)

    fireEvent.click(next)
    expect(screen.getByText('2/2')).not.toBeNull()
    expect(screen.getByText('Viz 2')).not.toBeNull()
  })

  it('regenerate passes the description of the version being viewed', () => {
    const onRegenerate = vi.fn()
    render(
      <ArtifactViz
        data={{ versions: [version(1), version(2)], active: 1 }}
        onRegenerate={onRegenerate}
      />
    )
    fireEvent.click(screen.getByLabelText('Previous version'))
    fireEvent.click(screen.getByText('↻ Regenerate'))
    expect(onRegenerate).toHaveBeenCalledWith('desc 1')
  })

  it('jumps to the new version when a regeneration adds one', () => {
    // Through VizBlock: the remount key that resets the view lives there.
    const json = (versions, active) =>
      JSON.stringify({ type: 'artifact', data: { versions, active } })
    const { rerender } = render(
      <VizBlock json={json([version(1), version(2)], 1)} />
    )
    fireEvent.click(screen.getByLabelText('Previous version'))
    expect(screen.getByText('1/2')).not.toBeNull()

    rerender(
      <VizBlock json={json([version(1), version(2), version(3)], 2)} />
    )
    expect(screen.getByText('3/3')).not.toBeNull()
    expect(screen.getByText('Viz 3')).not.toBeNull()
  })

  it('hides the regenerate button without a description', () => {
    render(
      <ArtifactViz data={{ title: 'T', html: '<p>x</p>' }} onRegenerate={() => {}} />
    )
    expect(screen.queryByText('↻ Regenerate')).toBeNull()
  })
})
