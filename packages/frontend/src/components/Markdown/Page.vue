<template>
  <markdown-field-content
    ref="mdeRef"
    @click="mdeRef?.focus()"
    class="mde-page"
    v-bind="$attrs" 
  />
</template>

<script setup lang="ts">
const mdeRef = useTemplateRef('mdeRef');

defineExpose({
  focus: () => mdeRef.value?.focus(),
  blur: () => mdeRef.value?.blur(),
})
</script>

<style lang="scss" scoped>
.mde-page:deep() {
  height: 100%;
  overflow-y: scroll;

  .mde {
    min-height: 100%;
  }

  .mde-footer {
    position: sticky;
    bottom: 0;
    width: 100%;
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
