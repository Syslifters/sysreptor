export default defineNuxtConfig({
  extends: ['..'],
  modules: ['@nuxt/eslint'],
  nitro: {
    output: {
      publicDir: 'dist',
    }
  },
})
