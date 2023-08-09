import { resolve } from 'path';
import { defineConfig } from '@vue/cli-service';
import CopyWebpackPlugin from 'copy-webpack-plugin';


export default defineConfig({
  runtimeCompiler: true,
  productionSourceMap: false,
  css: {
    extract: false,
    loaderOptions: {
      postcss: {
        postcssOptions: {
          plugins: [],
        }
      }
    }
  },
  configureWebpack: {
    optimization: {
      splitChunks: false,
      minimize: true,
    },
    output: {
      filename: 'bundle.js',
      asyncChunks: false,
    },
    resolve: {
      modules: [
        resolve('..', 'packages', 'markdown', 'node_modules')
      ],
      exportsFields: [],
    },
    plugins: [
      new CopyWebpackPlugin({
        patterns: [
          'NOTICE',
          'NOTICE_DESIGNS',
        ]
      })
    ]
  },
});

