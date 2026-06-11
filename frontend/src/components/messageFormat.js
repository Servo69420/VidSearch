// Pure, dependency-free text helpers for chat messages. Unit-tested in
// isolation (messageFormat.test.js).

// --- Reasoning / channel-token guard -------------------------------------
// The backend strips these at the source (chat.py:_strip_reasoning_tokens).
// This guard also cleans already-saved "dirty" history loaded from the DB on
// reload, and hardens against any surface form the backend misses.
const HARMONY_FINAL_RE = /<\|?channel\|?>\s*final\s*<\|?message\|?>([\s\S]*?)(?=<\|?(?:channel|start|end|return)\|?>|$)/gi
const HARMONY_SEGMENT_RE = /<\|?channel\|?>\s*(?:analysis|commentary|reasoning|thinking|thought)\b[\s\S]*?(?=<\|?(?:channel|start|end|return)\|?>|$)/gi
const THINK_BLOCK_RE = /<\s*(think|thinking|reasoning|reflection|thought)\s*>[\s\S]*?<\s*\/\s*\1\s*>/gi
const CONTROL_TOKEN_RE = /<\|?\s*\/?\s*(?:start|end|return|channel|message|constrain)\s*\|?>(?:\s*(?:assistant|developer|user|system))?/gi

// Code spans/fences (incl. ```vidviz``` artifact blocks) must pass through
// every prose transform untouched. Split on this and only transform the
// even-indexed (non-code) parts.
const CODE_SEGMENT_RE = /(```[\s\S]*?```|`[^`\n]*`)/g

export function applyOutsideCodeFences(text, fn) {
  if (!text) return text
  return text
    .split(CODE_SEGMENT_RE)
    .map((part, i) => (i % 2 === 1 ? part : fn(part)))
    .join('')
}

function stripReasoningSegment(s) {
  const finals = [...s.matchAll(HARMONY_FINAL_RE)].map(m => m[1].trim()).filter(Boolean)
  const out = finals.length ? finals.join('\n') : s.replace(HARMONY_SEGMENT_RE, '')
  return out.replace(THINK_BLOCK_RE, '').replace(CONTROL_TOKEN_RE, '')
}

export function stripReasoningTokens(text) {
  if (!text) return text
  return applyOutsideCodeFences(text, stripReasoningSegment).trim()
}

// --- Visualization blocks --------------------------------------------------
// ```vidviz fenced blocks embedded in assistant messages (rendered as
// interactive artifacts). Stripped before a (re)generated artifact replaces
// the old one in the message text.
const VIDVIZ_BLOCK_RE = /\n*```vidviz\b[\s\S]*?```\s*/gi

export function stripVidvizBlocks(text) {
  if (!text) return text
  return text.replace(VIDVIZ_BLOCK_RE, '').trim()
}

// --- Timestamp links -----------------------------------------------------
// Convert `12:34` style stamps into #seek: links, but SKIP code/artifact
// fences so HTML/JSON inside a ```vidviz``` block isn't corrupted.
const TIMESTAMP_RE = /\b(\d{1,2}:\d{2}(?::\d{2})?)\b/g

function timestampToSeconds(ts) {
  const parts = ts.split(':').map(Number)
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2]
  return parts[0] * 60 + parts[1]
}

export function injectTimestampLinks(text) {
  return applyOutsideCodeFences(text, (s) =>
    s.replace(TIMESTAMP_RE, (match) => `[${match}](#seek:${timestampToSeconds(match)})`)
  )
}

// --- LaTeX delimiter normalization ---------------------------------------
// KaTeX (remark-math) only fires on $...$ / $$...$$, but models often emit
// \(...\) and \[...\]. Convert them, but SKIP code spans/fences so backslash
// sequences inside code aren't corrupted.

function convertDelims(s) {
  return s
    // Display math: put $$ on their own lines so remark-math treats it as a
    // block (.katex-display), matching LaTeX's block semantics for \[...\].
    .replace(/\\\[([\s\S]*?)\\\]/g, (_, inner) => `$$\n${inner.trim()}\n$$`)
    .replace(/\\\(([\s\S]*?)\\\)/g, (_, inner) => `$${inner}$`)
}

export function normalizeMathDelimiters(text) {
  if (!text) return text
  // split() with a capturing group keeps the code segments at odd indices.
  return text
    .split(CODE_SEGMENT_RE)
    .map((part, i) => (i % 2 === 1 ? part : convertDelims(part)))
    .join('')
}
