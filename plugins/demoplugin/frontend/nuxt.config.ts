// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  extends: [
    '@sysreptor/plugin-base-layer',
  ],

  appConfig: {
    pluginId: 'db365aa0-ed36-4e90-93b6-a28effc4ed47',
  },

  srcDir: '.',
  nitro: {
    output: {
      publicDir: '../static/'
    }
  },
})
