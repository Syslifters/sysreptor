<template>
  <div class="mde-text-field-wrapper">
    <div 
      ref="editorRef" 
      v-intersect="onIntersect"
      class="mde-text-field" 
    />
  </div>
</template>

<script setup lang="js">
import {
  makeMarkdownEmits,
  makeMarkdownProps,
  markdownEditorTextFieldExtensions
} from "#imports";

const props = defineProps(makeMarkdownProps({
  spellcheckSupportedDefault: false
}));
const emit = defineEmits(makeMarkdownEmits());

const { onIntersect, focus, blur } = useMarkdownEditor({
  props: computed(() => props),
  emit,
  extensions: markdownEditorTextFieldExtensions(),
  fileUploadSupported: false,
});
defineExpose({
  focus,
  blur,
});
</script>

<style lang="scss" scoped>
@use "@base/assets/settings" as settings;

.mde-text-field, .mde-text-field-wrapper {
  width: 100%;
  max-width: 100%;
  display: inline-block;
  // color: color-mix(in srgb, rgb(var(--v-theme-on-background)) calc(var(--v-high-emphasis-opacity) * 100%), transparent);
}

:deep(.mde-text-field) {
  .cm-focused {
    outline: none !important;
  }

  .cm-content {
    font-family: settings.$body-font-family;
    padding: 0;
  }
  .cm-line {
    padding-left: 0;
  }

  .tok-todo {
    background-color: settings.$risk-color-critical;
    color: white;
    padding-left: 0.2em;
    padding-right: 0.2em;
    border-radius: 10%;
  }

  .cm-scroller {
    // Hide scrollbar
    overflow: hidden;
    // Prevent cutting off spellcheck error underline
    padding-bottom: 1px;
  }
}
</style>
