export function hashId(): string {
  return decodeURIComponent(location.hash.replace(/^#/, ''))
}

export function setHash(id: string | null) {
  const next = id
    ? `${location.pathname}${location.search}#${id}`
    : `${location.pathname}${location.search}`
  const current = `${location.pathname}${location.search}${location.hash}`
  if (current === next) return
  history.replaceState(history.state, '', next)
}

/** VitePress/GitHub-style slug so fragments stay stable and readable. */
export function slugifyFragment(text: string): string {
  return text
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

export function uniqueSlug(base: string, used: Set<string>, fallback = 'section'): string {
  let slug = base || fallback
  let n = 2
  while (used.has(slug)) {
    slug = `${base || fallback}-${n}`
    n += 1
  }
  used.add(slug)
  return slug
}
