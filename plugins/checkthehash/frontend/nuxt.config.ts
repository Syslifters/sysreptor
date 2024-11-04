// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  extends: [
    '@sysreptor/plugin-base-layer',
  ],

  appConfig: {
    pluginId: 'bfc0b269-4113-4b3c-b9f2-a150dae4abae',
  },

  nitro: {
    output: {
      publicDir: '../static/'
    }
  },
})
