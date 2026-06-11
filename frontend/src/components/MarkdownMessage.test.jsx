import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MarkdownMessage from './MarkdownMessage'

describe('MarkdownMessage', () => {
  describe('null/empty content', () => {
    it('returns nothing when content is null', () => {
      const { container } = render(<MarkdownMessage content={null} />)
      expect(container.firstChild).toBeNull()
    })

    it('returns nothing when content is undefined', () => {
      const { container } = render(<MarkdownMessage content={undefined} />)
      expect(container.firstChild).toBeNull()
    })

    it('returns nothing when content is an empty string', () => {
      const { container } = render(<MarkdownMessage content="" />)
      expect(container.firstChild).toBeNull()
    })
  })

  describe('inline formatting', () => {
    it('renders bold text as <strong>', () => {
      const { container } = render(<MarkdownMessage content="**bold text**" />)
      const strong = container.querySelector('strong')
      expect(strong).not.toBeNull()
      expect(strong.textContent).toBe('bold text')
    })

    it('renders italic text as <em>', () => {
      const { container } = render(<MarkdownMessage content="*italic text*" />)
      const em = container.querySelector('em')
      expect(em).not.toBeNull()
      expect(em.textContent).toBe('italic text')
    })

    it('renders triple-asterisk text as bold and italic', () => {
      const { container } = render(<MarkdownMessage content="***bold italic***" />)
      const strong = container.querySelector('strong')
      const em = container.querySelector('em')
      expect(strong).not.toBeNull()
      expect(em).not.toBeNull()
    })

    it('renders inline code as <code>', () => {
      const { container } = render(<MarkdownMessage content="use `console.log`" />)
      const code = container.querySelector('code')
      expect(code).not.toBeNull()
      expect(code.textContent).toBe('console.log')
    })
  })

  describe('code blocks', () => {
    it('renders a fenced code block as <pre><code>', () => {
      const content = '```\nconst x = 1\n```'
      const { container } = render(<MarkdownMessage content={content} />)
      const pre = container.querySelector('pre')
      const code = container.querySelector('pre code')
      expect(pre).not.toBeNull()
      expect(code).not.toBeNull()
    })
  })

  describe('lists', () => {
    it('renders an unordered list as <ul> with <li> items', () => {
      const content = '- item one\n- item two\n- item three'
      const { container } = render(<MarkdownMessage content={content} />)
      const ul = container.querySelector('ul')
      expect(ul).not.toBeNull()
      const items = container.querySelectorAll('li')
      expect(items).toHaveLength(3)
    })

    it('renders an ordered list as <ol> with <li> items', () => {
      const content = '1. first\n2. second\n3. third'
      const { container } = render(<MarkdownMessage content={content} />)
      const ol = container.querySelector('ol')
      expect(ol).not.toBeNull()
      const items = container.querySelectorAll('li')
      expect(items).toHaveLength(3)
    })
  })

  describe('headings', () => {
    it('renders # heading as <h1>', () => {
      const { container } = render(<MarkdownMessage content="# Heading One" />)
      const h1 = container.querySelector('h1')
      expect(h1).not.toBeNull()
      expect(h1.textContent).toBe('Heading One')
    })

    it('renders ## heading as <h2>', () => {
      const { container } = render(<MarkdownMessage content="## Heading Two" />)
      const h2 = container.querySelector('h2')
      expect(h2).not.toBeNull()
      expect(h2.textContent).toBe('Heading Two')
    })

    it('renders ### heading as <h3>', () => {
      const { container } = render(<MarkdownMessage content="### Heading Three" />)
      const h3 = container.querySelector('h3')
      expect(h3).not.toBeNull()
      expect(h3.textContent).toBe('Heading Three')
    })
  })

  describe('math (KaTeX)', () => {
    it('renders inline $x^3$ as a KaTeX element', () => {
      const { container } = render(<MarkdownMessage content="equation $x^3$ here" />)
      const katex = container.querySelector('.katex')
      expect(katex).not.toBeNull()
    })

    it('renders $$...$$ as a KaTeX display element', () => {
      const { container } = render(<MarkdownMessage content={'text\n\n$$\n\\frac{a}{b}\n$$\n\nmore'} />)
      const display = container.querySelector('.katex-display')
      expect(display).not.toBeNull()
    })

    it('leaves plain currency like $5 alone', () => {
      const { container } = render(<MarkdownMessage content="costs $5 total" />)
      expect(container.querySelector('.katex')).toBeNull()
      expect(container.textContent).toContain('$5')
    })
  })

  describe('LaTeX delimiter normalization', () => {
    it('renders \\(x^2\\) as a KaTeX element', () => {
      const { container } = render(<MarkdownMessage content={'value \\(x^2\\) here'} />)
      expect(container.querySelector('.katex')).not.toBeNull()
    })

    it('renders \\[a+b\\] as a KaTeX display element', () => {
      const { container } = render(<MarkdownMessage content={'text\n\n\\[a+b\\]\n\nmore'} />)
      expect(container.querySelector('.katex-display')).not.toBeNull()
    })
  })

  describe('reasoning-token guard', () => {
    it('hides leaked <think> reasoning, shows only the answer', () => {
      const { container } = render(
        <MarkdownMessage content={'<think>secret reasoning</think>The visible answer.'} />
      )
      expect(container.textContent).toContain('The visible answer.')
      expect(container.textContent).not.toContain('secret reasoning')
    })
  })

  describe('vidviz visualization blocks', () => {
    it('renders a topic-list block as clickable items that seek', async () => {
      const seeks = []
      const content =
        '```vidviz\n{"type":"topic-list","data":{"items":[{"label":"Intro","timestamp":12}]}}\n```'
      const { container } = render(
        <MarkdownMessage content={content} onTimestampClick={(s) => seeks.push(s)} />
      )
      const btn = container.querySelector('.vidviz-topic-item')
      expect(btn).not.toBeNull()
      expect(btn.textContent).toBe('Intro')
      btn.click()
      expect(seeks).toEqual([12])
    })

    it('falls back gracefully for an unknown viz type without throwing', () => {
      const content = '```vidviz\n{"type":"does-not-exist","data":{}}\n```'
      const { container } = render(<MarkdownMessage content={content} />)
      expect(container.querySelector('.vidviz-error')).not.toBeNull()
    })

    it('falls back gracefully for invalid JSON', () => {
      const content = '```vidviz\nnot json\n```'
      const { container } = render(<MarkdownMessage content={content} />)
      expect(container.querySelector('.vidviz-error')).not.toBeNull()
    })
  })

  describe('XSS safety', () => {
    it('does not execute script tags — renders them as escaped text', () => {
      const xssInput = "<script>alert('xss')</script>"
      const { container } = render(<MarkdownMessage content={xssInput} />)
      const scriptTags = container.querySelectorAll('script')
      expect(scriptTags).toHaveLength(0)
    })

    it('does not render img onerror as a DOM element with event handler', () => {
      const xssInput = '<img src=x onerror="alert(1)">'
      const { container } = render(<MarkdownMessage content={xssInput} />)
      const imgs = container.querySelectorAll('img[onerror]')
      expect(imgs).toHaveLength(0)
    })

    it('does not render javascript: href as a clickable link', () => {
      const xssInput = "[click me](javascript:alert(1))"
      const { container } = render(<MarkdownMessage content={xssInput} />)
      const links = container.querySelectorAll('a[href^="javascript:"]')
      expect(links).toHaveLength(0)
    })

    it('wraps content in a .markdown-message container div', () => {
      const { container } = render(<MarkdownMessage content="hello" />)
      const wrapper = container.querySelector('.markdown-message')
      expect(wrapper).not.toBeNull()
    })
  })
})
