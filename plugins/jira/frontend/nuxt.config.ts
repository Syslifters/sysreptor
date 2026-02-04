export default defineNuxtConfig({
  extends: [
    '@sysreptor/plugin-base-layer',
  ],

  appConfig: {
    pluginId: '2cb192a0-8591-4de6-aaea-656b44370a23',
  },

  srcDir: '.',
  nitro: {
    output: {
      publicDir: '../static/'
    },
  },
})
