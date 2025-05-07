<template>
  <markdown-diff-field-content
    class="mde-page"
    v-bind="attrs"
  />
</template>

<script setup lang="ts">
const attrs = useAttrs() as any;
</script>

<style lang="scss" scoped>
.mde-page:deep() {
  height: 100%;
  overflow-y: scroll;

  .mde {
    min-height: 100%;
  }

  .mde-editor {
    height: 100%;
  }
  .cm-content {
    font-family: monospace;
  }
  .cm-content, .cm-gutter { min-height: 0 !important; }
  .cm-lineNumbers {
    margin-bottom: 100vh;
  }
}
</style>
