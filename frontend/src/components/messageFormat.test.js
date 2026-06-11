import { describe, it, expect } from 'vitest'
import { stripReasoningTokens, normalizeMathDelimiters, stripVidvizBlocks } from './messageFormat'

describe('stripVidvizBlocks', () => {
  const block = '```vidviz\n{"type":"artifact","data":{"title":"T","description":"d","html":"<p>x</p>"}}\n```'

  it('removes a trailing artifact block, keeping the text', () => {
    expect(stripVidvizBlocks(`The answer.\n\n${block}`)).toBe('The answer.')
  })

  it('removes a block that is the entire message', () => {
    expect(stripVidvizBlocks(block)).toBe('')
  })

  it('leaves other code fences untouched', () => {
    const text = 'Look:\n\n```js\nconst a = 1\n```'
    expect(stripVidvizBlocks(text)).toBe(text)
  })

  it('returns empty/falsy input unchanged', () => {
    expect(stripVidvizBlocks('')).toBe('')
    expect(stripVidvizBlocks(null)).toBe(null)
  })
})

describe('stripReasoningTokens', () => {
  it('keeps only the final Harmony channel', () => {
    const input =
      '<|channel|>analysis<|message|>let me think<|end|>' +
      '<|start|>assistant<|channel|>final<|message|>The capital is Paris.'
    expect(stripReasoningTokens(input)).toBe('The capital is Paris.')
  })

  it('drops a non-final analysis segment when no final channel exists', () => {
    const input = '<|channel|>analysis<|message|>internal musing<|end|>The answer.'
    expect(stripReasoningTokens(input)).toBe('The answer.')
  })

  it('strips <think> blocks', () => {
    expect(stripReasoningTokens('<think>reasoning</think>Answer is 42.')).toBe('Answer is 42.')
  })

  it('strips malformed pipe variants', () => {
    expect(stripReasoningTokens('<|channel>thought here<channel|>Real reply.')).toBe('Real reply.')
  })

  it('strips stray control tokens and trailing role word', () => {
    expect(stripReasoningTokens('<|start|>assistant<|message|>Hi.<|end|>')).toBe('Hi.')
  })

  it('leaves normal text unchanged', () => {
    const text = 'A plain answer with no reasoning tokens.'
    expect(stripReasoningTokens(text)).toBe(text)
  })

  it('returns empty/falsy input unchanged', () => {
    expect(stripReasoningTokens('')).toBe('')
    expect(stripReasoningTokens(null)).toBe(null)
  })
})

describe('normalizeMathDelimiters', () => {
  it('converts inline \\(...\\) to $...$', () => {
    expect(normalizeMathDelimiters('value \\(x^2\\) here')).toBe('value $x^2$ here')
  })

  it('converts display \\[...\\] to block $$...$$', () => {
    expect(normalizeMathDelimiters('\\[a+b\\]')).toBe('$$\na+b\n$$')
  })

  it('leaves $...$ and plain text untouched', () => {
    expect(normalizeMathDelimiters('cost is $5 and $x$ math')).toBe('cost is $5 and $x$ math')
  })

  it('does NOT transform delimiters inside an inline code span', () => {
    expect(normalizeMathDelimiters('use `\\(x\\)` literally')).toBe('use `\\(x\\)` literally')
  })

  it('does NOT transform delimiters inside a fenced code block', () => {
    const input = '```\nf(\\(x\\))\n```'
    expect(normalizeMathDelimiters(input)).toBe(input)
  })

  it('returns empty/falsy input unchanged', () => {
    expect(normalizeMathDelimiters('')).toBe('')
    expect(normalizeMathDelimiters(undefined)).toBe(undefined)
  })
})
