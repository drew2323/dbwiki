/**
 * Compare two Tiptap documents: documents are flattened to one text line per
 * block, diffed line by line (LCS), and changed line pairs get a word diff.
 */

export type DiffKind = 'equal' | 'add' | 'del'

export interface DiffOp {
  type: DiffKind
  text: string
}

export interface WordPart {
  type: DiffKind
  text: string
}

export interface DiffRow {
  kind: 'equal' | 'add' | 'del' | 'change'
  /** text for equal/add/del rows */
  text?: string
  /** word level parts for 'change' rows (old line -> new line) */
  parts?: WordPart[]
}

const inlineText = (node: any): string => {
  if (!node) return ''
  if (typeof node.text === 'string') return node.text
  if (node.type === 'hardBreak') return ' '
  if (node.type === 'image') return `[image${node.attrs?.alt ? `: ${node.attrs.alt}` : ''}]`
  return Array.isArray(node.content) ? node.content.map(inlineText).join('') : ''
}

/** One line per block: headings keep their level, list items their bullet, tables one line per row */
export const tiptapToLines = (doc: any): string[] => {
  const lines: string[] = []

  const walk = (node: any, prefix = '') => {
    if (!node) return
    const children: any[] = Array.isArray(node.content) ? node.content : []

    switch (node.type) {
      case 'doc':
        children.forEach((c) => walk(c, prefix))
        return
      case 'heading':
        lines.push(`${'#'.repeat(Number(node.attrs?.level) || 1)} ${inlineText(node)}`.trimEnd())
        return
      case 'paragraph': {
        const t = inlineText(node)
        if (t.trim() || prefix) lines.push(`${prefix}${t}`.trimEnd())
        return
      }
      case 'bulletList':
        children.forEach((c) => walk(c, `${prefix}• `))
        return
      case 'orderedList':
        children.forEach((c, i) => walk(c, `${prefix}${i + 1}. `))
        return
      case 'listItem': {
        // first block of the item carries the bullet, further blocks are indented
        children.forEach((c, i) => walk(c, i === 0 ? prefix : ' '.repeat(prefix.length)))
        return
      }
      case 'blockquote':
        children.forEach((c) => walk(c, `${prefix}> `))
        return
      case 'codeBlock':
        inlineText(node).split('\n').forEach((l) => lines.push(`${prefix}    ${l}`.trimEnd()))
        return
      case 'horizontalRule':
        lines.push('---')
        return
      case 'image':
        lines.push(inlineText(node))
        return
      case 'table':
        children.forEach((row) => walk(row, prefix))
        return
      case 'tableRow':
        lines.push(children.map((cell) => inlineText(cell).trim()).join(' | '))
        return
      default:
        if (children.length) children.forEach((c) => walk(c, prefix))
        else if (typeof node.text === 'string') lines.push(node.text)
    }
  }

  walk(doc)
  return lines
}

const MAX_CELLS = 4_000_000

/** Line diff via longest common subsequence; huge inputs degrade to replace-all */
export const diffLines = (a: string[], b: string[]): DiffOp[] => {
  // trim common head/tail first - most edits touch a small part of the page
  let start = 0
  while (start < a.length && start < b.length && a[start] === b[start]) start++
  let endA = a.length
  let endB = b.length
  while (endA > start && endB > start && a[endA - 1] === b[endB - 1]) {
    endA--
    endB--
  }

  const head: DiffOp[] = a.slice(0, start).map((text) => ({ type: 'equal', text }))
  const tail: DiffOp[] = a.slice(endA).map((text) => ({ type: 'equal', text }))
  const x = a.slice(start, endA)
  const y = b.slice(start, endB)

  let middle: DiffOp[]
  if ((x.length + 1) * (y.length + 1) > MAX_CELLS) {
    middle = [...x.map((text): DiffOp => ({ type: 'del', text })), ...y.map((text): DiffOp => ({ type: 'add', text }))]
  } else {
    const w = y.length + 1
    const lcs = new Uint32Array((x.length + 1) * w)
    for (let i = x.length - 1; i >= 0; i--) {
      for (let j = y.length - 1; j >= 0; j--) {
        lcs[i * w + j] = x[i] === y[j] ? lcs[(i + 1) * w + j + 1] + 1 : Math.max(lcs[(i + 1) * w + j], lcs[i * w + j + 1])
      }
    }
    middle = []
    let i = 0
    let j = 0
    while (i < x.length && j < y.length) {
      if (x[i] === y[j]) {
        middle.push({ type: 'equal', text: x[i] })
        i++
        j++
      } else if (lcs[(i + 1) * w + j] >= lcs[i * w + j + 1]) {
        middle.push({ type: 'del', text: x[i++] })
      } else {
        middle.push({ type: 'add', text: y[j++] })
      }
    }
    while (i < x.length) middle.push({ type: 'del', text: x[i++] })
    while (j < y.length) middle.push({ type: 'add', text: y[j++] })
  }

  return [...head, ...middle, ...tail]
}

/** Word level diff of two lines (whitespace is kept as its own token) */
export const diffWords = (before: string, after: string): WordPart[] => {
  const tokenize = (s: string) => s.split(/(\s+)/).filter((t) => t !== '')
  const ops = diffLines(tokenize(before), tokenize(after))
  const parts: WordPart[] = []
  for (const op of ops) {
    const last = parts[parts.length - 1]
    if (last && last.type === op.type) last.text += op.text
    else parts.push({ type: op.type, text: op.text })
  }
  return parts
}

/** Merge a run of removed lines followed by added lines into word-diffed 'change' rows */
export const buildDiffRows = (before: any, after: any): DiffRow[] => {
  const ops = diffLines(tiptapToLines(before), tiptapToLines(after))
  const rows: DiffRow[] = []

  let i = 0
  while (i < ops.length) {
    if (ops[i].type === 'equal') {
      rows.push({ kind: 'equal', text: ops[i].text })
      i++
      continue
    }
    const dels: string[] = []
    const adds: string[] = []
    while (i < ops.length && ops[i].type === 'del') dels.push(ops[i++].text)
    while (i < ops.length && ops[i].type === 'add') adds.push(ops[i++].text)
    // adds that precede dels (LCS may emit either order) belong to the same change block
    while (i < ops.length && ops[i].type === 'del') dels.push(ops[i++].text)

    const paired = Math.min(dels.length, adds.length)
    for (let k = 0; k < paired; k++) rows.push({ kind: 'change', parts: diffWords(dels[k], adds[k]) })
    for (let k = paired; k < dels.length; k++) rows.push({ kind: 'del', text: dels[k] })
    for (let k = paired; k < adds.length; k++) rows.push({ kind: 'add', text: adds[k] })
  }
  return rows
}

export const summarizeRows = (rows: DiffRow[]) => {
  let added = 0
  let removed = 0
  for (const r of rows) {
    if (r.kind === 'add') added++
    else if (r.kind === 'del') removed++
    else if (r.kind === 'change') {
      added++
      removed++
    }
  }
  return { added, removed, changed: added > 0 || removed > 0 }
}
