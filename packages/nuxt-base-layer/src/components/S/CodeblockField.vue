<template>
  <v-textarea
    auto-grow
    :persistent-hint="true"
    hide-details="auto"
    :max-errors="100"
    spellcheck="false"
    autocomplete="off"
    class="textarea-codeblock"
  >
    <template #label v-if="$slots.label"><slot name="label" /></template>
  </v-textarea>
</template>

<style lang="scss" scoped>
@use "@base/assets/vuetify.scss" as vuetify;

.textarea-codeblock {
  :deep(textarea) {
    font-family: monospace;
    line-height: 1.2em;
    font-size: medium;
    background-color: vuetify.$code-background-color;
    color: vuetify.$code-color;
  }
}
</style>
