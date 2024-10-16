import { fileURLToPath } from 'url'
import { dirname, join } from 'path'

const currentDir = dirname(fileURLToPath(import.meta.url))

export default defineNuxtConfig({
  // Build as SPA application
  ssr: false,
  
  sourcemap: {
    client: true,
  },
  buildId: 'static',

  alias: {
    '@base': currentDir,
  },

  css: [
    'vuetify/styles',
    join(currentDir, './assets/global.scss'),
    '@mdi/font/css/materialdesignicons.css',
  ],

  modules: [
    '@nuxt/eslint',
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
        configFile: join(currentDir, './assets/vuetify.scss'),
      }
    },
    vuetifyOptions: join(currentDir, './vuetify.config.ts'),
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
  compatibilityDate: '2024-07-08',

});
