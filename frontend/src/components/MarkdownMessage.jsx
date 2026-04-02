import { memo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './MarkdownMessage.css'

// SECURITY: Do NOT add rehype-raw here. It enables raw HTML passthrough which
// opens XSS vectors. If richer HTML output is ever needed, add rehype-sanitize
// alongside it. The default config (no rehype plugins) is the safe choice.
const MarkdownMessage = memo(function MarkdownMessage({ content }) {
  if (!content) return null
  return (
    <div className="markdown-message">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {content}
      </ReactMarkdown>
    </div>
  )
})

export default MarkdownMessage
