import { createProxyServer } from "httpxy"

const isDev = process.env.NODE_ENV === 'development';

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  // Build as SPA application
  ssr: false,
  // Source code directory
  srcDir: 'src/',
  dir: {
    public: 'src/public/'
  },
  sourcemap: {
    client: true,
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

  css: [
    'vuetify/styles',
    '@/assets/global.scss',
    '@mdi/font/css/materialdesignicons.css',
  ],

  modules: [
    ['@nuxtjs/eslint-module', { lintOnStart: false }],
    'vuetify-nuxt-module',
    '@vueuse/nuxt',
    '@pinia/nuxt',
    '@pinia-plugin-persistedstate/nuxt',
  ],

  piniaPersistedstate: {
    storage: 'localStorage'
  },

  vuetify: {
    moduleOptions: {
      styles: {
        configFile: 'assets/vuetify.scss',
      }
    },
    vuetifyOptions: 'src/vuetify.config.ts',
  },

  build: {
    transpile: ['vue-toastification'],
  },

  experimental: {
    payloadExtraction: false,
  },
  future: {
    compatibilityVersion: 4,
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
        },
        '/ws': {
          target: 'ws://api:8000',
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
      }
    },
  },
  hooks: {
    // Websocket proxy workaround: https://github.com/nuxt/cli/issues/107#issuecomment-1850751905
    listen(server) {
      const proxy = createProxyServer({ target: { host: "api", port: 8000 }, ws: true })

      server.removeAllListeners("upgrade")
      server.on("upgrade", (req, socket, head) => {
        if (req.url!.startsWith('/ws')) {
          // @ts-ignore
          proxy.ws(req, socket, head);
        }
      })
    },
  },

});
