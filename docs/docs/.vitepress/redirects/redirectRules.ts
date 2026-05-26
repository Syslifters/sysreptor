export type RedirectsMap = Record<string, string>

export type RedirectRule =
  | {
      kind: 'exact'
      from: string
      to: string
    }
  | {
      kind: 'prefix'
      fromPrefix: string
      toPrefix: string
    }

function _ensureLeadingSlash(p: string): string {
  if (!p) return '/'
  return p.startsWith('/') ? p : `/${p}`
}

function _stripTrailingSlashExceptRoot(p: string): string {
  if (p === '/') return '/'
  return p.endsWith('/') ? p.replace(/\/+$/, '') : p
}

function _normalizePathForMatch(p: string): string {
  return _stripTrailingSlashExceptRoot(_ensureLeadingSlash(p.trim()))
}

function _isWildcardDirRule(p: string): boolean {
  return p.endsWith('/*')
}

function _isExternalUrl(p: string): boolean {
  return p.startsWith('http://') || p.startsWith('https://')
}

function _asDirPrefix(p: string): string {
  // "/old/*" should match "/old/<suffix>" only, not "/older"
  // Normalize "/old/" -> "/old" then append "/"
  const base = _normalizePathForMatch(p.slice(0, -2))
  return base === '/' ? '/' : `${base}/`
}

function _pushRedirectRule(rules: RedirectRule[], fromRaw: string, toRaw: string) {
  const from = _ensureLeadingSlash(fromRaw)
  const to = toRaw.startsWith('/') || _isExternalUrl(toRaw)
    ? toRaw
    : _ensureLeadingSlash(toRaw)

  if (_isWildcardDirRule(from)) {
    if (!_isWildcardDirRule(to)) {
      // Require symmetry for now: /a/* -> /b/*
      return
    }
    rules.push({
      kind: 'prefix',
      fromPrefix: _asDirPrefix(from),
      toPrefix: _asDirPrefix(to),
    })
    return
  }

  rules.push({
    kind: 'exact',
    from: _normalizePathForMatch(from),
    to: _isWildcardDirRule(to) || _isExternalUrl(to) ? to : _normalizePathForMatch(to),
  })
}

function _sortRedirectRules(rules: RedirectRule[]) {
  // Prefer exact matches over prefixes; prefer longer prefixes first.
  rules.sort((a, b) => {
    if (a.kind !== b.kind) return a.kind === 'exact' ? -1 : 1
    if (a.kind === 'prefix' && b.kind === 'prefix') {
      return b.fromPrefix.length - a.fromPrefix.length
    }
    return 0
  })
}

export function redirectsFromMap(map: RedirectsMap): RedirectRule[] {
  const rules: RedirectRule[] = []

  for (const [fromRaw, toRaw] of Object.entries(map)) {
    if (!fromRaw || !toRaw) continue
    _pushRedirectRule(rules, fromRaw, toRaw)
  }

  _sortRedirectRules(rules)
  return rules
}

export function matchRedirect(pathname: string, rules: RedirectRule[]): string | null {
  const p = _normalizePathForMatch(pathname)

  for (const rule of rules) {
    if (rule.kind === 'exact') {
      if (p === rule.from) return rule.to
      continue
    }

    // prefix rule
    if (rule.fromPrefix === '/') {
      // Degenerate: "/*" (not recommended) - treat as no-op
      continue
    }

    // Match both "/old" and "/old/" by checking normalized p plus "/"
    const pAsDir = p === '/' ? '/' : `${p}/`
    if (!pAsDir.startsWith(rule.fromPrefix)) continue

    const suffix = pAsDir.slice(rule.fromPrefix.length) // may be empty or include nested segments ending with "/"
    const suffixTrimmed = suffix.endsWith('/') ? suffix.slice(0, -1) : suffix
    const target = rule.toPrefix + suffixTrimmed
    return _stripTrailingSlashExceptRoot(target)
  }

  return null
}

