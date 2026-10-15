/**
 * Render Tiptap JSON to HTML for read-only page views.
 *
 * Content is user supplied and shown to every reader (including anonymous
 * visitors of public spaces), so everything is escaped and URLs are limited
 * to safe schemes. Do not interpolate raw node text/attrs into HTML anywhere
 * else.
 */

const ESCAPES: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;'
}

export const escapeHtml = (value: unknown): string =>
  String(value ?? '').replace(/[&<>"']/g, (c) => ESCAPES[c])

/** http(s), mailto, tel, in-page (#) and same-site relative (/) URLs only */
export const safeUrl = (url: unknown): string | null => {
  if (typeof url !== 'string') return null
  const trimmed = url.trim()
  if (!trimmed) return null
  // Browsers ignore tabs/newlines/control chars inside the scheme ("java\nscript:")
  const normalised = trimmed.replace(/[\u0000- ]/g, '')
  if (/^(https?:|mailto:|tel:)/i.test(normalised)) return trimmed
  if (/^\/(?!\/)/.test(normalised) || normalised.startsWith('#')) return trimmed
  return null
}

const isExternal = (url: string) => /^https?:/i.test(url.trim())

const intAttr = (value: unknown): number | null => {
  const n = Number(value)
  return Number.isInteger(n) && n > 1 && n < 1000 ? n : null
}

export const renderTiptap = (json: any): string => {
  if (!json) return ''

  let headingIndex = 0

  const renderMarks = (text: string, marks: any[] | undefined): string => {
    let out = text
    for (const mark of marks || []) {
      switch (mark?.type) {
        case 'bold':
          out = `<strong>${out}</strong>`
          break
        case 'italic':
          out = `<em>${out}</em>`
          break
        case 'underline':
          out = `<u>${out}</u>`
          break
        case 'code':
          out = `<code>${out}</code>`
          break
        case 'strike':
          out = `<s>${out}</s>`
          break
        case 'link': {
          const href = safeUrl(mark.attrs?.href)
          if (href) {
            const external = isExternal(href) ? ' target="_blank" rel="noopener noreferrer nofollow"' : ''
            out = `<a href="${escapeHtml(href)}" class="text-primary hover:underline"${external}>${out}</a>`
          }
          break
        }
      }
    }
    return out
  }

  const renderNode = (node: any): string => {
    if (!node) return ''

    if (node.type === 'text' || typeof node.text === 'string') {
      return renderMarks(escapeHtml(node.text), node.marks)
    }

    const children = Array.isArray(node.content) ? node.content.map(renderNode).join('') : ''

    switch (node.type) {
      case 'doc':
        return children
      case 'paragraph':
        return `<p>${children || '<br>'}</p>`
      case 'heading': {
        const level = Math.min(6, Math.max(1, Number(node.attrs?.level) || 1))
        // IDs are what the outline panel scrolls to
        return `<h${level} id="heading-${headingIndex++}">${children}</h${level}>`
      }
      case 'bulletList':
        return `<ul>${children}</ul>`
      case 'orderedList':
        return `<ol>${children}</ol>`
      case 'listItem':
        return `<li>${children}</li>`
      case 'codeBlock':
        return `<pre><code>${children}</code></pre>`
      case 'blockquote':
        return `<blockquote>${children}</blockquote>`
      case 'horizontalRule':
        return '<hr>'
      case 'hardBreak':
        return '<br>'
      case 'image': {
        const src = safeUrl(node.attrs?.src)
        if (!src) return ''
        return `<img src="${escapeHtml(src)}" alt="${escapeHtml(node.attrs?.alt || '')}" loading="lazy" class="max-w-full h-auto rounded" />`
      }
      case 'table':
        return `<table class="border-collapse table-auto w-full"><tbody>${children}</tbody></table>`
      case 'tableRow':
        return `<tr>${children}</tr>`
      case 'tableHeader':
      case 'tableCell': {
        const tag = node.type === 'tableHeader' ? 'th' : 'td'
        const colspan = intAttr(node.attrs?.colspan)
        const rowspan = intAttr(node.attrs?.rowspan)
        const attrs = `${colspan ? ` colspan="${colspan}"` : ''}${rowspan ? ` rowspan="${rowspan}"` : ''}`
        return `<${tag}${attrs}>${children}</${tag}>`
      }
      default:
        return children
    }
  }

  return renderNode(json)
}
