import { fileURLToPath } from 'url'
import { dirname, join } from 'path'

const currentDir = dirname(fileURLToPath(import.meta.url))

export default defineNuxtConfig({
  future: {
    compatibilityVersion: 4,
  },
  compatibilityDate: '2025-08-26',
  devtools: { enabled: false },

  // Build as SPA application
  ssr: false,
  
  sourcemap: {
    client: true,
  },
  srcDir: join(currentDir, './src'),
  watch: [
    join(currentDir, './src'),
  ],

  alias: {
    '@base': join(currentDir, './src'),
  },

  modules: [
    '@nuxt/eslint',
    'vuetify-nuxt-module',
    '@vueuse/nuxt',
    '@pinia/nuxt',
    'pinia-plugin-persistedstate/nuxt',
  ],

  css: [
    // 'vuetify/styles',
    join(currentDir, './src/assets/global.scss'),
    '@mdi/font/css/materialdesignicons.css',
  ],

  piniaPluginPersistedstate: {
    storage: 'localStorage',
  },

  vuetify: {
    moduleOptions: {
      styles: {
        configFile: join(currentDir, './src/assets/vuetify.scss'),
      }
    },
    vuetifyOptions: join(currentDir, './src/vuetify.config.ts'),
  },

  // build: {
  //   transpile: ['vue-toastification'],
  // },

  vite: {
    resolve: {
      dedupe: ['vuetify'],
    },
    optimizeDeps: {
      include: [
        'js-file-download', 'base64-arraybuffer', 'uuid', 'zxcvbn', 'emoji-mart-vue-fast/src',
        'vue-toastification', 'date-fns', 'lodash-es', 'url-join',
      ],
    },
  },

  experimental: {
    payloadExtraction: false,
  },
});
