import { fileURLToPath, URL } from 'node:url'
import { defineConfig, PluginOption } from 'vite'
import vue from '@vitejs/plugin-vue'
import cssInjectedByJsPlugin from "vite-plugin-css-injected-by-js";
import { viteStaticCopy } from 'vite-plugin-static-copy'


export default defineConfig({
  plugins: [
    vue(),
    cssInjectedByJsPlugin(),
    viteStaticCopy({
      targets: [{
        src: ['NOTICE', 'NOTICE_DESIGNS'],
        dest: '',
      }],
    }),
  ] as unknown as PluginOption[],
  resolve: {
    alias: {
      vue: 'vue/dist/vue.esm-bundler.js',
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  build: {
    assetsDir: '',
    sourcemap: false,
    minify: 'esbuild',
    lib: {
      entry: 'src/main.ts',
      formats: ['iife'],
      name: 'rendering',
      fileName: () => 'bundle.js',
    },
  },
  define: {
    'process.env': {
      NODE_ENV: 'development',
    },
  },
});
