import { createElement } from 'react'
import TopicListViz from './TopicListViz'
import ArtifactViz from './ArtifactViz'

// type string -> React component. Register future interactive visualizations
// here. The renderer (MarkdownMessage) dispatches through VizBlock only.
const VIZ_REGISTRY = {
  'topic-list': TopicListViz,
  'artifact': ArtifactViz,
}

export function VizBlock({ json, onTimestampClick, onRegenerate }) {
  let spec
  try {
    spec = JSON.parse(json)
  } catch {
    return <pre className="vidviz-error">Invalid visualization data</pre>
  }
  const component = spec && VIZ_REGISTRY[spec.type]
  if (!component) {
    return <pre className="vidviz-error">Unsupported visualization: {String(spec?.type ?? 'none')}</pre>
  }
  // Remount the component when a regeneration changes the version list, so a
  // fresh mount shows the spec's active version (its view state resets).
  const versionCount = Array.isArray(spec.data?.versions) ? spec.data.versions.length : 1
  const specKey = `v${versionCount}-${spec.data?.active ?? 0}`
  // createElement (rather than <Component/>) keeps the registry lookup out of
  // JSX so the static-components lint rule sees a stable component reference.
  return (
    <div className="vidviz">
      {createElement(component, {
        key: specKey,
        data: spec.data,
        onTimestampClick,
        onRegenerate,
      })}
    </div>
  )
}
