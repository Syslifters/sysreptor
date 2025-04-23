import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
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
  ],
  resolve: {
    alias: {
      vue: 'vue/dist/vue.esm-bundler.js',
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      // Use a modified version of "@vue/compiler-core" that supports parsing tag content as raw text
      // See package.json postinstall script for installation and patching
      // When updating Vue, make sure that the patch still works
      // Checkout vue-core, apply patches, run "nr build" and "nr build-dts", copy packages/compiler-core/dist/{compiler-core.esm-bundler.js,compiler-core.d.ts} to node_modules/@vue/compiler-core/dist/, run npx patch-package @vue/compiler-core
      '@vue/compiler-core': fileURLToPath(new URL('node_modules/@vue/compiler-core/dist/compiler-core.esm-bundler.js', import.meta.url)),
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
