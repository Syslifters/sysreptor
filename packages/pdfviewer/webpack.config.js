const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');


exports.default = {
  mode: "none",
  devtool: 'source-map',
  plugins: [
    new HtmlWebpackPlugin({
      filename: 'viewer.html',
      template: path.join(__dirname, "./src/viewer.html"),
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
