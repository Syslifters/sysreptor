import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { viteStaticCopy } from 'vite-plugin-static-copy'

// https://vitejs.dev/config/
export default defineConfig({
  base: './',
  build: {
    outDir: '../static',
    emptyOutDir: true,
  },
  plugins: [
    react(),
    viteStaticCopy({
      targets: [
        {
          src: '../../node_modules/@excalidraw/excalidraw/dist/prod/fonts/',
          dest: '',
        }
      ]
    }),
  ],
})
