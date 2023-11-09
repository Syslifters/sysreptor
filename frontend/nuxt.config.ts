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
        { rel: 'icon', type: 'image/x-icon', href: '/static/favicon.ico' }
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
    inlineSSRStyles: false,
    payloadExtraction: false,
  },

  // Dev settings
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
        '/admin': 'http://api:8000',
        '/static': {
          target: 'http://api:8000',
          bypass(req) {
            if (['/static/logo.svg', '/static/favicon.ico'].includes(req.url!) || req.url!.startsWith('/static/pdfviewer/')) {
              return req.url;
            }
          },
        },
      }
    },
  },

});
