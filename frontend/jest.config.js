const path = require('path');

module.exports = {
  // preset: '@nuxt/test-utils',
  moduleDirectories: [
    "node_modules",
    "<rootDir>/node_modules",
    "<rootDir>/node_modules/reportcreator-markdown/node_modules",
  ],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
    '^~/(.*)$': '<rootDir>/$1',
    '^vue$': 'vue/dist/vue.common.js',
    '\\.(css|less|scss|sass)$': '<rootDir>/test/__mocks__/styleMock.js',
    '\\.(svg)$': '<rootDir>/test/__mocks__/styleMock.js',
    '^micromark-extension-directive/lib/factory-attributes.js$': '<rootDir>/node_modules/reportcreator-markdown/node_modules/micromark-extension-directive/lib/factory-attributes.js',
  },
  moduleFileExtensions: [
    "js", 
    "vue",
    "json",
  ],
  transformIgnorePatterns: [
    '<rootDir>/node_modules/(?!(url-join|vuetify|uuid)/.*)',
  ],
  transform: {
    '^.+\\.js$': [
      'babel-jest',
      {
        presets: [
          ['@babel/preset-env', { targets: { node: "current" } }],
        ],
        // plugins: ['@babel/plugin-transform-runtime']
      }
    ],
    '.*\\.(vue)$': '@vue/vue2-jest'
  },
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: [path.resolve(__dirname, 'test/jest.setup.js')],

  collectCoverage: false,
  collectCoverageFrom: [
    '<rootDir>/components/**/*.vue',
    '<rootDir>/pages/**/*.vue',
    '<rootDir>/utils/**/*.js',
  ],

  reporters: [
    'default',
    ['jest-junit', {
      outputDirectory: './test-reports',
      outputName: 'junit.xml',
    }],
  ],
};
