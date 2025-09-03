import { createProxyServer } from "httpxy"
import type { IncomingMessage, ServerResponse } from "http";

const isDev = process.env.NODE_ENV === 'development';

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  extends: ['@sysreptor/nuxt-base-layer'],

  future: {
    compatibilityVersion: 4,
  },
  compatibilityDate: '2025-08-26',

  // Source code directory
  srcDir: 'src/',
  dir: {
    public: 'src/public/'
  },

  app: {
    buildAssetsDir: isDev ? '_nuxt' : '/static/_nuxt/',
    head: {
      htmlAttrs: {
        lang: 'en'
      },
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'format-detection', content: 'telephone=no' },
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/static/favicon.ico' },
      ],
    }
  },

  // Dev settings
  devtools: {
    enabled: false,
  },
  devServer: {
    port: 3000,
  },
  vite: {
    resolve: {
      conditions: ['module', 'worker', 'browser', 'development|production'],
    },
    optimizeDeps: {
      include: [
        'vuedraggable', 'monaco-editor', '@github/webauthn-json/browser-ponyfill', 'randomcolor', '@elastic/apm-rum-vue',
        // Dependencies of @sysreptor/markdown
        '@codemirror/state', '@codemirror/view', '@codemirror/commands', '@codemirror/lint', '@codemirror/autocomplete', 
        '@codemirror/search', '@codemirror/merge', '@codemirror/language', '@codemirror/lang-vue', '@codemirror/lang-css', 
        '@codemirror/lang-html', '@lezer/common', '@lezer/highlight', 'crelt', 'mermaid', 'micromark', 'unified', 
        'remark-parse', 'remark-rehype', 'rehype-remark', 'remark-stringify', 'rehype-parse', 'rehype-raw', 'rehype-sanitize', 
        'hast-util-to-mdast', 'micromark-util-chunked', 'micromark-util-symbol', 'micromark-util-resolve-all', 'unist-util-visit', 
        'micromark-extension-gfm-strikethrough', 'mdast-util-gfm-strikethrough', 'micromark-extension-gfm-task-list-item', 
        'mdast-util-gfm-task-list-item', 'parse-entities', 'micromark-util-sanitize-uri', 'micromark-extension-gfm-table', 
        'mdast-util-gfm-table', 'hast-util-to-string', 'lowlight', 'html-void-elements', 'property-information', 
        'stringify-entities', 'micromark-factory-space', 'micromark-factory-whitespace', 'micromark-util-character', 
        'micromark-factory-destination', 'micromark-factory-label', 'micromark-factory-title', 'micromark-util-normalize-identifier',
      ],
    },
    worker: {
      format: 'es',
    },
    server: {
      proxy: {
        '/api': {
          target: 'http://api:8000',
          changeOrigin: false,
          ws: true,
        },
        '/admin': {
          target: 'http://api:8000',
          changeOrigin: false,
        },
        '/__debug__': {
          target: 'http://api:8000',
          changeOrigin: false,
        },
        '/static': {
          target: 'http://api:8000',
          changeOrigin: false,
          bypass(req) {
            if (['/static/logo.svg', '/static/logo-text.svg', '/static/favicon.ico'].includes(req.url!) || req.url!.startsWith('/static/pdfviewer/')) {
              return req.url;
            }
          },
        },
        '/favicon.ico': {
          target: 'http://api:8000',
          changeOrigin: false,
        },
      }
    },
  },
  hooks: {
    // Websocket proxy workaround: https://github.com/nuxt/cli/issues/107#issuecomment-1850751905
    listen(server) {
      const proxy = createProxyServer({ target: { host: "api", port: 8000 }, ws: true })

      server.removeAllListeners("upgrade")
      server.on("upgrade", (req: IncomingMessage, socket: ServerResponse, head: any) => {
        if (req.url!.startsWith('/api')) {
          proxy.ws(req, socket, head);
        }
      })
    },
  },

});

