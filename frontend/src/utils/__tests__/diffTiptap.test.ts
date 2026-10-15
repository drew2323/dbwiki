import { describe, it, expect } from 'vitest'
import { tiptapToLines, diffLines, diffWords, buildDiffRows, summarizeRows } from '../diffTiptap'

const t = (text: string) => ({ type: 'text', text })
const p = (text: string) => ({ type: 'paragraph', content: text ? [t(text)] : [] })
const doc = (...content: any[]) => ({ type: 'doc', content })

describe('tiptapToLines', () => {
  it('flattens blocks to lines and keeps structure markers', () => {
    const lines = tiptapToLines(doc(
      { type: 'heading', attrs: { level: 2 }, content: [t('Title')] },
      p('Hello'),
      p(''),
      { type: 'bulletList', content: [{ type: 'listItem', content: [p('one')] }, { type: 'listItem', content: [p('two')] }] },
      { type: 'orderedList', content: [{ type: 'listItem', content: [p('first')] }] },
      { type: 'codeBlock', content: [t('a\nb')] },
      { type: 'image', attrs: { src: '/x', alt: 'logo' } }
    ))
    expect(lines).toEqual(['## Title', 'Hello', '• one', '• two', '1. first', '    a', '    b', '[image: logo]'])
  })

  it('renders table rows as pipe separated cells', () => {
    const lines = tiptapToLines(doc({
      type: 'table',
      content: [{ type: 'tableRow', content: [
        { type: 'tableHeader', content: [p('A')] },
        { type: 'tableCell', content: [p('B')] }
      ] }]
    }))
    expect(lines).toEqual(['A | B'])
  })

  it('handles empty and null documents', () => {
    expect(tiptapToLines(null)).toEqual([])
    expect(tiptapToLines(doc())).toEqual([])
  })
})

describe('diffLines', () => {
  it('detects insertions, deletions and keeps order', () => {
    const ops = diffLines(['a', 'b', 'c', 'd'], ['a', 'c', 'x', 'd'])
    expect(ops.map((o) => `${o.type[0]}:${o.text}`)).toEqual(['e:a', 'd:b', 'e:c', 'a:x', 'e:d'])
  })

  it('returns only equal ops for identical input', () => {
    expect(diffLines(['a', 'b'], ['a', 'b']).every((o) => o.type === 'equal')).toBe(true)
  })

  it('handles empty sides', () => {
    expect(diffLines([], ['a'])).toEqual([{ type: 'add', text: 'a' }])
    expect(diffLines(['a'], [])).toEqual([{ type: 'del', text: 'a' }])
    expect(diffLines([], [])).toEqual([])
  })

  it('degrades gracefully for very large inputs', () => {
    const a = Array.from({ length: 3000 }, (_, i) => `a${i}`)
    const b = Array.from({ length: 3000 }, (_, i) => `b${i}`)
    const ops = diffLines(a, b)
    expect(ops.filter((o) => o.type === 'del')).toHaveLength(3000)
    expect(ops.filter((o) => o.type === 'add')).toHaveLength(3000)
  })
})

describe('diffWords', () => {
  it('marks only the changed words', () => {
    const parts = diffWords('the quick brown fox', 'the slow brown fox')
    expect(parts.filter((p) => p.type === 'del').map((p) => p.text)).toEqual(['quick'])
    expect(parts.filter((p) => p.type === 'add').map((p) => p.text)).toEqual(['slow'])
    expect(parts.map((p) => p.text).join('')).toBe('the quickslow brown fox')
  })
})

describe('buildDiffRows', () => {
  it('pairs replaced lines into word-level change rows', () => {
    const rows = buildDiffRows(doc(p('keep'), p('old text')), doc(p('keep'), p('new text'), p('added')))
    expect(rows.map((r) => r.kind)).toEqual(['equal', 'change', 'add'])
    expect(summarizeRows(rows)).toEqual({ added: 2, removed: 1, changed: true })
  })

  it('reports no change for identical documents', () => {
    const d = doc(p('same'))
    expect(summarizeRows(buildDiffRows(d, d)).changed).toBe(false)
  })

  it('works when a version is empty', () => {
    const rows = buildDiffRows(null, doc(p('first')))
    expect(rows).toEqual([{ kind: 'add', text: 'first' }])
  })
})
