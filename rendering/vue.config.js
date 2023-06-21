// const LicenseWebpackPlugin = require('license-webpack-plugin').LicenseWebpackPlugin;
// const resolve = require('path').resolve;
import {LicenseWebpackPlugin} from 'license-webpack-plugin';
import {resolve} from 'path';
import {licenseTextOverrides as markdownLicenseTextOverrides} from 'reportcreator-markdown/licenseInfos.js';
import { defineConfig } from '@vue/cli-service';

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
      new LicenseWebpackPlugin({
        perChunkOutput: false,
        outputFilename: 'NOTICE',
        excludedPackageTest: packageName => ['reportcreator-rendering', 'reportcreator-markdown'].includes(packageName),
        unacceptableLicenseTest: licenseType => ![
          'Apache-2.0', 'MIT', 'BSD-2-Clause', 'BSD-3-Clause', 'ISC',
          '(MPL-2.0 OR Apache-2.0)', '(MIT AND BSD-3-Clause)'
        ].includes(licenseType),
        licenseTypeOverrides: {
          'chart.js-auto': 'MIT',
        },
        licenseTextOverrides: {
          ...markdownLicenseTextOverrides,
          'chart.js-auto': `The MIT License (MIT)

Copyright (c) 2014-2022 Chart.js Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy 
of this software and associated documentation files (the "Software"), to deal 
in the Software without restriction, including without limitation the rights 
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
copies of the Software, and to permit persons to whom the Software is 
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN 
THE SOFTWARE.`,
        }
      }),
    ]
  },
});
