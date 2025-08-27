// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  extends: [
    '@sysreptor/plugin-base-layer',
  ],

  appConfig: {
    pluginId: 'ebfbb193-c108-4b80-bd6a-a97a86ba9c8f',
  },

  nitro: {
    output: {
      publicDir: '../static/'
    }
  },
})
