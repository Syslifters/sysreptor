const isDev = process.env.NODE_ENV === 'development';

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  // Build as SPA application
  ssr: false,
  // Source code directory
  srcDir: 'src/',
  sourcemap: {
    client: true,
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

  css: [
    'vuetify/styles',
    '@/assets/global.scss',
    '@mdi/font/css/materialdesignicons.css',
  ],

  modules: [
    ['@nuxtjs/eslint-module', { lintOnStart: false }],
    'vuetify-nuxt-module',
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
        // '/ws': {
        //   // TODO: proxy does not forward WebSocket requests to target
        //   target: 'ws://api:8000',
        //   changeOrigin: true,
        //   ws: true,
        //   secure: false,
        //   configure: (proxy, _options) => {
        //     console.log('Configuring WebSocket Proxy');
        //     proxy.on('error', (err, _req, _res) => {
        //       console.log('proxy error', err);
        //     });
        //     proxy.on('proxyReq', (proxyReq, req, _res) => {
        //       console.log('Sending Request to the Target:', req.method, req.url);
        //     });
        //     proxy.on('proxyRes', (proxyRes, req, _res) => {
        //       console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
        //     });
        //     proxy.on('proxyReqWs', (proxyReq, req, socket, options, head) => {
        //       console.log('Sending WebSocket Request to the Target:', req.url);
        //     });
        //   },
        // },

        '/admin': 'http://api:8000',
        '/static': {
          target: 'http://api:8000',
          bypass(req) {
            if (['/static/logo.svg', '/static/logo-text.svg', '/static/favicon.ico'].includes(req.url!) || req.url!.startsWith('/static/pdfviewer/')) {
              return req.url;
            }
          },
        },
      }
    },
  },

});
