// Demo visualization proving the vidviz seam end-to-end.
// data shape: { items: [{ label: string, timestamp: number }] }
function TopicListViz({ data, onTimestampClick }) {
  const items = Array.isArray(data?.items) ? data.items : []
  if (!items.length) return null
  return (
    <ul className="vidviz-topic-list">
      {items.map((item, i) => (
        <li key={i}>
          <button
            type="button"
            className="vidviz-topic-item"
            onClick={() => onTimestampClick?.(item.timestamp)}
          >
            {item.label}
          </button>
        </li>
      ))}
    </ul>
  )
}

export default TopicListViz
