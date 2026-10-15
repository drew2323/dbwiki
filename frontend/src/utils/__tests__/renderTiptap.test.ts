import { describe, it, expect } from 'vitest'
import { renderTiptap, safeUrl, escapeHtml } from '../renderTiptap'

const doc = (...content: any[]) => ({ type: 'doc', content })
const p = (...content: any[]) => ({ type: 'paragraph', content })
const text = (t: string, marks?: any[]) => ({ type: 'text', text: t, ...(marks ? { marks } : {}) })

describe('escapeHtml', () => {
  it('escapes markup characters', () => {
    expect(escapeHtml(`<a href="x">&'</a>`)).toBe('&lt;a href=&quot;x&quot;&gt;&amp;&#39;&lt;/a&gt;')
  })
})

describe('safeUrl', () => {
  it.each([
    ['https://example.com/a?b=1', true],
    ['http://example.com', true],
    ['mailto:a@b.cz', true],
    ['/api/attachments/1/file', true],
    ['#heading-2', true],
    ['javascript:alert(1)', false],
    ['  JaVaScRiPt:alert(1)', false],
    ['java\nscript:alert(1)', false],
    ['data:text/html,<script>alert(1)</script>', false],
    ['//evil.example.com', false],
    ['', false]
  ])('%s -> allowed=%s', (url, allowed) => {
    expect(safeUrl(url) !== null).toBe(allowed)
  })

  it('rejects non-strings', () => {
    expect(safeUrl(undefined)).toBeNull()
    expect(safeUrl({})).toBeNull()
  })
})

describe('renderTiptap', () => {
  it('returns empty string without content', () => {
    expect(renderTiptap(null)).toBe('')
  })

  it('escapes text so it cannot inject HTML', () => {
    const html = renderTiptap(doc(p(text('<img src=x onerror=alert(1)>'))))
    expect(html).toBe('<p>&lt;img src=x onerror=alert(1)&gt;</p>')
  })

  it('applies marks around escaped text', () => {
    const html = renderTiptap(doc(p(text('a<b', [{ type: 'bold' }, { type: 'italic' }]))))
    expect(html).toBe('<p><em><strong>a&lt;b</strong></em></p>')
  })

  it('drops javascript: links but keeps their text', () => {
    const html = renderTiptap(doc(p(text('click', [{ type: 'link', attrs: { href: 'javascript:alert(1)' } }]))))
    expect(html).toBe('<p>click</p>')
  })

  it('makes external links safe to open', () => {
    const html = renderTiptap(doc(p(text('x', [{ type: 'link', attrs: { href: 'https://example.com' } }]))))
    expect(html).toContain('href="https://example.com"')
    expect(html).toContain('rel="noopener noreferrer nofollow"')
    expect(html).toContain('target="_blank"')
  })

  it('cannot break out of attributes via image src/alt', () => {
    const html = renderTiptap(doc({ type: 'image', attrs: { src: '/x.png', alt: '"><script>alert(1)</script>' } }))
    expect(html).not.toContain('<script>')
    expect(html).toContain('alt="&quot;&gt;&lt;script&gt;alert(1)&lt;/script&gt;"')
  })

  it('omits images with unsafe sources', () => {
    expect(renderTiptap(doc({ type: 'image', attrs: { src: 'javascript:alert(1)' } }))).toBe('')
  })

  it('numbers headings consecutively for the outline', () => {
    const html = renderTiptap(doc(
      { type: 'heading', attrs: { level: 1 }, content: [text('A')] },
      { type: 'heading', attrs: { level: 9 }, content: [text('B')] }
    ))
    expect(html).toBe('<h1 id="heading-0">A</h1><h6 id="heading-1">B</h6>')
  })

  it('renders tables with header cells, colspans and escaped content', () => {
    const html = renderTiptap(doc({
      type: 'table',
      content: [{
        type: 'tableRow',
        content: [
          { type: 'tableHeader', attrs: { colspan: 2 }, content: [p(text('H'))] },
          { type: 'tableCell', attrs: { colspan: '"><x' }, content: [p(text('<C>'))] }
        ]
      }]
    }))
    expect(html).toContain('<th colspan="2"><p>H</p></th>')
    expect(html).toContain('<td><p>&lt;C&gt;</p></td>')
  })

  it('renders lists and code blocks', () => {
    const html = renderTiptap(doc(
      { type: 'bulletList', content: [{ type: 'listItem', content: [p(text('one'))] }] },
      { type: 'codeBlock', content: [text('a < b')] }
    ))
    expect(html).toBe('<ul><li><p>one</p></li></ul><pre><code>a &lt; b</code></pre>')
  })
})
