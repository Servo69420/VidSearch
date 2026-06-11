import { memo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'
import { stripReasoningTokens, normalizeMathDelimiters, injectTimestampLinks } from './messageFormat'
import { VizBlock } from './viz/registry'
import './MarkdownMessage.css'

// SECURITY: Do NOT add rehype-raw here. It enables raw HTML passthrough which
// opens XSS vectors. If richer HTML output is ever needed, add rehype-sanitize
// alongside it. The default config (no rehype plugins) is the safe choice.
const MarkdownMessage = memo(function MarkdownMessage({
  content,
  onTimestampClick,
  onVizRegenerate,
  messageIndex,
}) {
  if (!content) return null

  // Order matters: strip control tokens first, normalize math, then links.
  let processed = stripReasoningTokens(content)
  processed = normalizeMathDelimiters(processed)
  if (onTimestampClick) processed = injectTimestampLinks(processed)
  if (!processed) return null

  const components = {
    // Intercept ```vidviz fenced blocks at the <pre> level (avoids invalid
    // nesting) and dispatch to the viz registry. Everything else falls through.
    pre({ children, ...props }) {
      const child = Array.isArray(children) ? children[0] : children
      const className = child?.props?.className || ''
      if (/language-vidviz/.test(className)) {
        return (
          <VizBlock
            json={String(child.props.children)}
            onTimestampClick={onTimestampClick}
            onRegenerate={
              onVizRegenerate
                ? (description) => onVizRegenerate(messageIndex, description)
                : undefined
            }
          />
        )
      }
      return <pre {...props}>{children}</pre>
    },
    a({ href, children }) {
      if (onTimestampClick && href?.startsWith('#seek:')) {
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
  }

  return (
    <div className="markdown-message">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={components}
      >
        {processed}
      </ReactMarkdown>
    </div>
  )
})

export default MarkdownMessage
