/* eslint-disable quote-props */
module.exports = {
  root: true,
  env: {
    browser: true,
    node: true
  },
  parserOptions: {
    parser: '@babel/eslint-parser',
    requireConfigFile: false
  },
  extends: [
    '@nuxtjs',
    'plugin:nuxt/recommended'
  ],
  plugins: [
  ],
  // add your custom rules here
  rules: {
    "comma-dangle": "off",
    "semi": "off",
    "vue/multi-word-component-names": "off",
    "space-before-function-paren": "off",
    "vue/singleline-html-element-content-newline": "off",
    "no-trailing-spaces": "off",
    "vue/max-attributes-per-line": "off",
    "vue/attributes-order": "off",
    "multiline-ternary": "off",
    "operator-linebreak": "off",
    "quotes": "off",
    "vue/html-self-closing": "off",
    "vue/valid-v-slot": "off",

    "no-unused-vars": "warn",
    "vue/no-unused-components": "warn",
    "eol-last": "warn",
    "no-multiple-empty-lines": "warn",
    "object-curly-spacing": "warn",
    "prefer-const": "warn",
  }
}
