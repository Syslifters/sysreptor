export type ChatStrings = {
  title: string
  greeting: string
  suggestions: string[]
  disclaimer: string
  placeholder: string
  send: string
  /** Labels for known SSE `delta.status` values. Unknown keys are humanized. */
  statuses: Record<string, string>
  copy: string
  copied: string
  expand: string
  collapse: string
  reset: string
  close: string
  open: string
  error: string
  rateLimitedWait: string
  rateLimitedError: string
  askAi: string
}

const en: ChatStrings = {
  title: 'AI Assistant',
  greeting: 'How can I help you today?',
  suggestions: [
    'Why is reporting with SysReptor so easy?',
    'How do I install SysReptor?',
    'Can I integrate SysReptor with Python?',
  ],
  disclaimer: "AI might make mistakes. Don't share personal information.",
  placeholder: 'Type a message…',
  send: 'Send',
  statuses: {
    retrieving: 'Retrieving context',
    thinking: 'Thinking',
    searching: 'Searching',
  },
  copy: 'Copy',
  copied: 'Copied',
  expand: 'Expand',
  collapse: 'Collapse',
  reset: 'Reset chat',
  close: 'Close',
  open: 'Ask AI',
  error: 'Something went wrong. Please try again.',
  rateLimitedWait: 'Too many requests. Retrying in {n}s',
  rateLimitedError: 'Too many requests. Please try again in a moment.',
  askAi: 'Ask AI',
}

/** Turn an unknown status key into a readable label (e.g. `web_search` → `Web search`). */
export function humanizeStatus(status: string): string {
  const spaced = status.replace(/[_-]+/g, ' ').trim()
  if (!spaced) return status
  return spaced.charAt(0).toUpperCase() + spaced.slice(1)
}

export function statusLabel(strings: ChatStrings, status: string): string {
  return strings.statuses[status] ?? humanizeStatus(status)
}

/** Resolve BCP-47 / path lang to a supported UI locale. */
export function isGermanLocale(lang: string | undefined | null): boolean {
  return (lang || '').toLowerCase().startsWith('de')
}

export function getChatStrings(lang?: string | null): ChatStrings {
  return en
}

/**
 * Prefer an explicit locale prop, then `<html lang>`, then English.
 * Works outside VitePress without `useData()`.
 */
export function resolveLocale(explicit?: string | null): string {
  if (explicit) return explicit
  if (typeof document !== 'undefined') {
    return document.documentElement.lang || 'en'
  }
  return 'en'
}
