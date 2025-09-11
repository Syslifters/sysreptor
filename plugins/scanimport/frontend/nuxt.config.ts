export default defineNuxtConfig({
  extends: [
    '@sysreptor/plugin-base-layer',
  ],

  appConfig: {
    pluginId: '2335e86b-198c-4e6c-9563-8190a05ee38c',
  },

  nitro: {
    output: {
      publicDir: '../static/'
    },
  },

  vite: {
    optimizeDeps: {
      include: ['@he-tree/vue'],
    },
  },
})
