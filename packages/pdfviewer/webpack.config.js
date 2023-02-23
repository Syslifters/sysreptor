const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');


exports.default = {
  mode: "none",
  devtool: 'source-map',
  plugins: [
    new HtmlWebpackPlugin({
      filename: 'viewer.html',
      template: path.join(__dirname, "./src/viewer.html"),
    }),
    new CopyWebpackPlugin({
      patterns: [
        'node_modules/pdfjs-dist/build/pdf.js.map',
        'node_modules/pdfjs-dist/build/pdf.worker.js.map'
      ]
    }),
  ],
  module: {
    rules: [
      {
        test: /\.css$/i,
        use: ['style-loader', 'css-loader'],
      },
    ],
  },
  output: {
    path: path.join(__dirname, 'dist'),
    filename: '[name].[contenthash].js',
    clean: true,
  },
}
