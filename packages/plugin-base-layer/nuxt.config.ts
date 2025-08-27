import { fileURLToPath } from 'url'
import { dirname, join } from 'path'

const currentDir = dirname(fileURLToPath(import.meta.url));

export default defineNuxtConfig({
  extends: [
    '@sysreptor/nuxt-base-layer',
  ],

  compatibilityDate: '2025-08-26',
  srcDir: join(currentDir, './src'),
  watch: [
    join(currentDir, './src'),
  ],

  app: {
    cdnURL: './',
  },

  router: {
    options: {
      hashMode: true
    }
  },

  nitro: {
    output: {
      publicDir: '../static/'
    }
  },
})
