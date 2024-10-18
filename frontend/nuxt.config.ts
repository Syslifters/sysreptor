import { createProxyServer } from "httpxy"
import type { IncomingMessage, ServerResponse } from "http";

const isDev = process.env.NODE_ENV === 'development';

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  extends: ['nuxt-base-layer'],

  future: {
    compatibilityVersion: 4,
  },
  compatibilityDate: '2024-07-08',

  // Source code directory
  srcDir: 'src/',
  dir: {
    public: 'src/public/'
  },

  buildId: 'static',
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
