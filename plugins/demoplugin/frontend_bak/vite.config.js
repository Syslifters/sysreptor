import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
  ],
  build: {
    lib: {
      entry: './src/index.js',
      formats: ['es'],
      fileName: 'index',
    },
    outDir: '../static',
    emptyOutDir: true,
    sourcemap: true,
    rollupOptions: {
      external: ['vue'],
      // output: {
      //   globals: {
      //     vue: 'vue',
      //   }
      // }
    },
  }
})
