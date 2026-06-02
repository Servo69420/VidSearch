const PROTECTED_MARKDOWN_RE = /(```[\s\S]*?```|`[^`\n]*`|\$\$[\s\S]*?\$\$|\$[^$\n]+\$)/g

const LATEX_CONTROL_RE = String.raw`\\(?:alpha|beta|gamma|delta|epsilon|varepsilon|theta|vartheta|lambda|mu|pi|rho|sigma|tau|phi|varphi|omega|Delta|Theta|Lambda|Pi|Sigma|Phi|Omega|circ|degree|sqrt|frac|angle|sin|cos|tan|log|ln|cdot|times|div|pm|mp|leq|geq|neq|approx|infty|sum|int|lim)`
const LATEX_ATOM_RE = String.raw`(?:[A-Za-z0-9]+|\\[A-Za-z]+|\{[^}]+\})`

const BRACKET_INLINE_RE = /\\\(([\s\S]*?)\\\)/g
const BRACKET_DISPLAY_RE = /\\\[([\s\S]*?)\\\]/g
const FRACTION_RE = new RegExp(`(^|[^\\w$\\\`])((?:${LATEX_CONTROL_RE}\\s*)?\\\\frac\\{[^}]+\\}\\{[^}]+\\}(?:\\s*[_^]\\s*(?:${LATEX_ATOM_RE}))?)`, 'g')
const ROOT_RE = new RegExp(`(^|[^\\w$\\\`])((?:[A-Za-z0-9]+\\s*)?\\\\sqrt(?:\\[[^\\]]+\\])?\\{[^}]+\\})`, 'g')
const STANDALONE_COMMAND_RE = new RegExp(`(^|[^\\w$\\\`_^])(${LATEX_CONTROL_RE}(?:\\s*[_^]\\s*(?:${LATEX_ATOM_RE}))?)`, 'g')
const SUPER_SUB_RE = new RegExp(`(^|[^\\w$\\\`])((?:${LATEX_ATOM_RE})(?:\\s*[_^]\\s*(?:${LATEX_ATOM_RE}))+)(?=$|[^\\w])`, 'g')
const MATH_HINT_RE = new RegExp(`(?:${LATEX_CONTROL_RE}|(?:${LATEX_ATOM_RE})\\s*[_^]\\s*(?:${LATEX_ATOM_RE})|[°∠√±×÷∞≈≠≤≥α-ωΑ-Ω])`)

function wrapBareMath(text, regex) {
  return text.replace(regex, (match, prefix, math) => {
    if (!math || math.includes('$')) return match
    return `${prefix}$${math.trim()}$`
  })
}

function normalizeTextMath(text) {
  return wrapBareMath(
    wrapBareMath(
      wrapBareMath(
        wrapBareMath(
          text
            .replace(BRACKET_DISPLAY_RE, (_, math) => `$$${math.trim()}$$`)
            .replace(BRACKET_INLINE_RE, (_, math) => `$${math.trim()}$`),
          FRACTION_RE
        ),
        ROOT_RE
      ),
      SUPER_SUB_RE
    ),
    STANDALONE_COMMAND_RE
  )
}

export function normalizeMarkdownMath(content) {
  if (typeof content !== 'string' || !content) return content

  const parts = []
  let lastIndex = 0
  for (const match of content.matchAll(PROTECTED_MARKDOWN_RE)) {
    if (match.index > lastIndex) {
      parts.push(normalizeTextMath(content.slice(lastIndex, match.index)))
    }
    parts.push(match[0])
    lastIndex = match.index + match[0].length
  }
  if (lastIndex < content.length) {
    parts.push(normalizeTextMath(content.slice(lastIndex)))
  }
  return parts.join('')
}

export function looksLikeMathExpression(value) {
  return typeof value === 'string' && MATH_HINT_RE.test(value)
}

export function normalizeLatexSource(value) {
  if (typeof value !== 'string') return value
  return value
    .replace(/\$(.*?)\$/g, '$1')
    .replace(/\\\(([\s\S]*?)\\\)/g, '$1')
    .replace(/\\\[([\s\S]*?)\\\]/g, '$1')
    .replace(/(\d)\s*°/g, String.raw`$1^{\circ}`)
    .replace(/°/g, String.raw`^{\circ}`)
}
