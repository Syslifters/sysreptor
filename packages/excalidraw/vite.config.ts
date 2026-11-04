import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { viteStaticCopy } from 'vite-plugin-static-copy'

// https://vitejs.dev/config/
export default defineConfig({
  base: './',
  resolve: {
    dedupe: ['react', 'react-dom'],
  },
  plugins: [
    react(),
    viteStaticCopy({
      targets: [
        {
          src: '../node_modules/@excalidraw/excalidraw/dist/prod/fonts/**/*',
          dest: 'fonts',
          rename: { stripBase: 6 },
        },
      ],
    }),
  ],
  build: {
    target: 'es2022',
  },
})
