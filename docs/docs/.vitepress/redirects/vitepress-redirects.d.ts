import type { RedirectsMap } from './redirectRules'

declare module 'vitepress' {
  interface UserConfig {
    /**
     * URL redirects for dev/preview servers.
     *
     * @example
     * redirects: {
     *   '/old-page': '/new-page',
     *   '/old-dir/*': '/new-dir/*',
     * }
     */
    redirects?: RedirectsMap
  }
}

declare global {
  // Set by VitePress during `resolveConfig()`
  // eslint-disable-next-line no-var
  var VITEPRESS_CONFIG: import('vitepress').SiteConfig | undefined
}

export {}
