import path from 'path'
import type { Plugin } from 'vite'
import { matchRedirect, redirectsFromMap, type RedirectRule, type RedirectsMap } from './redirectRules'

const VIRTUAL_ID = 'virtual:vitepress-redirects'
const RESOLVED_VIRTUAL_ID = '\0' + VIRTUAL_ID

export type VitepressRedirectsPluginOptions = {
  redirects?: RedirectsMap
  statusCode?: 301 | 302 | 307 | 308
}

function _redirectsFromVitepressConfig(opts: VitepressRedirectsPluginOptions): RedirectsMap {
  if (opts.redirects) return opts.redirects
  return globalThis.VITEPRESS_CONFIG?.userConfig?.redirects ?? {}
}

function _parsePathname(url: string): { pathname: string; search: string } {
  // req.url is typically like "/foo?bar=1"
  const q = url.indexOf('?')
  if (q === -1) return { pathname: url || '/', search: '' }
  return { pathname: url.slice(0, q) || '/', search: url.slice(q) }
}

export function vitepressRedirectsPlugin(
  opts: VitepressRedirectsPluginOptions = {}
): Plugin {
  const statusCode = opts.statusCode ?? 301

  let rules: RedirectRule[] = []

  function refreshRules() {
    rules = redirectsFromMap(_redirectsFromVitepressConfig(opts))
  }

  function applyMiddleware(server: any) {
    refreshRules()

    server.middlewares.use((req: any, res: any, next: any) => {
      const method = String(req.method || 'GET').toUpperCase()
      if (method !== 'GET' && method !== 'HEAD') return next()

      const rawUrl = String(req.url || '/')
      const { pathname, search } = _parsePathname(rawUrl)
      const target = matchRedirect(pathname, rules)
      if (!target) return next()

      res.statusCode = statusCode
      res.setHeader('Location', target + search)
      res.end()
    })
  }

  return {
    name: 'syslifters:vitepress-redirects',
    enforce: 'pre',

    configResolved() {
      refreshRules()
    },

    resolveId(id) {
      if (id === VIRTUAL_ID) return RESOLVED_VIRTUAL_ID
      return null
    },

    load(id) {
      if (id !== RESOLVED_VIRTUAL_ID) return null
      refreshRules()
      return [
        `export const rules = ${JSON.stringify(rules)};`,
        `export default rules;`,
      ].join('\n')
    },

    configureServer(server) {
      applyMiddleware(server)
    },

    // Also handle `vitepress preview`
    configurePreviewServer(server) {
      applyMiddleware(server)
    },

    handleHotUpdate(ctx) {
      const configDeps = globalThis.VITEPRESS_CONFIG?.configDeps ?? []
      const changed = path.resolve(ctx.file)
      if (!configDeps.some((dep) => path.resolve(dep) === changed)) return

      refreshRules()

      const mod = ctx.server.moduleGraph.getModuleById(RESOLVED_VIRTUAL_ID)
      if (mod) ctx.server.moduleGraph.invalidateModule(mod)
      ctx.server.ws.send({ type: 'full-reload' })
    },
  }
}
