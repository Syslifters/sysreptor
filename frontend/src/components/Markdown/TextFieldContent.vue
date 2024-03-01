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
} from "~/composables/markdown";

const props = defineProps(makeMarkdownProps({
  files: false,
  spellcheckSupportedDefault: false
}));
const emit = defineEmits(makeMarkdownEmits());

const { onIntersect, focus, blur } = useMarkdownEditor({
  props: computed(() => props),
  emit,
  extensions: markdownEditorTextFieldExtensions(),
});
defineExpose({
  focus,
  blur,
});
</script>

<style lang="scss" scoped>
@use "@/assets/settings" as settings;

.mde-text-field, .mde-text-field-wrapper {
  width: 100%;
  max-width: 100%;
  display: inline-block;
  //color: rgba(var(--v-theme-on-background), var(--v-high-emphasis-opacity));
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
