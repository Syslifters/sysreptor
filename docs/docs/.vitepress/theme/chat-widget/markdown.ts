import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  typographer: false,
})

const DOCS_HOST = 'docs.sysreptor.com'

function isDocsHref(href: string | null): boolean {
  if (!href) return false
  try {
    return new URL(href, `https://${DOCS_HOST}/`).hostname === DOCS_HOST
  } catch {
    return false
  }
}

const defaultLinkOpen =
  md.renderer.rules.link_open ||
  ((tokens, idx, options, _env, self) => self.renderToken(tokens, idx, options))

md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  const token = tokens[idx]
  if (!isDocsHref(token.attrGet('href'))) {
    token.attrSet('target', '_blank')
    token.attrSet('rel', 'noopener noreferrer')
  }
  return defaultLinkOpen(tokens, idx, options, env, self)
}

const defaultFence =
  md.renderer.rules.fence ||
  ((tokens, idx, options, _env, self) => self.renderToken(tokens, idx, options))

md.renderer.rules.fence = (tokens, idx, options, env, self) => {
  const token = tokens[idx]
  const info = (token.info || '').trim()
  const lang = info.split(/\s+/g)[0] || ''
  const rendered = defaultFence(tokens, idx, options, env, self)
  const label = lang || 'code'
  return (
    `<div class="sys-chat-codeblock">` +
    `<div class="sys-chat-codeblock-bar">` +
    `<span class="sys-chat-codeblock-lang">${md.utils.escapeHtml(label)}</span>` +
    `<button type="button" class="sys-chat-copy-btn" data-copy="code">Copy</button>` +
    `</div>${rendered}</div>`
  )
}

export function renderChatMarkdown(source: string): string {
  const html = md.render(source || '')
  return DOMPurify.sanitize(html, {
    USE_PROFILES: { html: true },
    ADD_ATTR: ['data-copy', 'target', 'rel'],
  })
}

export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    try {
      const ta = document.createElement('textarea')
      ta.value = text
      ta.setAttribute('readonly', '')
      ta.style.position = 'fixed'
      ta.style.left = '-9999px'
      document.body.appendChild(ta)
      ta.select()
      const ok = document.execCommand('copy')
      document.body.removeChild(ta)
      return ok
    } catch {
      return false
    }
  }
}
