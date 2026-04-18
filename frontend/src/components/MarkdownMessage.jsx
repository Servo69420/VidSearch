import { memo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './MarkdownMessage.css'

const TIMESTAMP_RE = /\b(\d{1,2}:\d{2}(?::\d{2})?)\b/g

function timestampToSeconds(ts) {
  const parts = ts.split(':').map(Number)
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2]
  return parts[0] * 60 + parts[1]
}

function injectTimestampLinks(text) {
  return text.replace(TIMESTAMP_RE, (match) => {
    const secs = timestampToSeconds(match)
    return `[${match}](#seek:${secs})`
  })
}

// SECURITY: Do NOT add rehype-raw here. It enables raw HTML passthrough which
// opens XSS vectors. If richer HTML output is ever needed, add rehype-sanitize
// alongside it. The default config (no rehype plugins) is the safe choice.
const MarkdownMessage = memo(function MarkdownMessage({ content, onTimestampClick }) {
  if (!content) return null

  const processed = onTimestampClick ? injectTimestampLinks(content) : content

  const components = onTimestampClick ? {
    a({ href, children }) {
      if (href?.startsWith('#seek:')) {
        const secs = parseInt(href.slice(6), 10)
        return (
          <button
            className="md-timestamp"
            onClick={() => onTimestampClick(secs)}
            type="button"
          >
            {children}
          </button>
        )
      }
      return <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>
    },
  } : undefined

  return (
    <div className="markdown-message">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {processed}
      </ReactMarkdown>
    </div>
  )
})

export default MarkdownMessage
