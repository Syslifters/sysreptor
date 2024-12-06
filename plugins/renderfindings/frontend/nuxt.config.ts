// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  extends: [
    '@sysreptor/plugin-base-layer',
  ],

  appConfig: {
    pluginId: '62d0f5ae-5c07-47c6-9203-a9d9c3dbffb2',
  },

  nitro: {
    output: {
      publicDir: '../static/'
    }
  },
})
