// @ts-check
import withNuxt from './.nuxt/eslint.config.mjs'

export default withNuxt({
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
        "func-call-spacing": "off",

        // "no-unused-vars": "warn",
        "@typescript-eslint/no-unused-vars": "warn",
        "vue/no-unused-components": "warn",
        "eol-last": "warn",
        "no-multiple-empty-lines": "warn",
        "object-curly-spacing": "warn",
        "prefer-const": "warn",
    }
})
