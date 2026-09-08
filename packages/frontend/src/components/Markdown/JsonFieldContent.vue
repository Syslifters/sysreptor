<template>
  <div class="json-field-wrapper">
    <div
      ref="editorRef"
      v-intersect="onIntersect"
      class="json-field"
    />
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue';
import { forceLinting, jsonSchemaLinter } from '@sysreptor/markdown/editor';
import {
  makeMarkdownEmits,
  makeMarkdownProps,
  jsonEditorDefaultExtensions,
  useMarkdownEditor,
} from '@/composables/markdown';

const props = defineProps({
  ...makeMarkdownProps({
    spellcheckSupportedDefault: false,
  }),
  schema: {
    type: Object as PropType<Record<string, any>|null>,
    default: null,
  },
});
const emit = defineEmits(makeMarkdownEmits());

const { onIntersect, focus, blur, editorView } = useMarkdownEditor({
  props: computed(() => props),
  emit,
  extensions: [
    ...jsonEditorDefaultExtensions(),
    jsonSchemaLinter(() => props.schema),
  ],
  fileUploadSupported: false,
});

watch(() => props.schema, () => {
  if (editorView.value) {
    forceLinting(editorView.value);
  }
});

defineExpose({
  focus,
  blur,
});
</script>

<style lang="scss" scoped>
@use "sass:meta";

.json-field, .json-field-wrapper {
  width: 100%;
  max-width: 100%;
  display: inline-block;
}

:deep(.json-field) {
  @include meta.load-css("@/assets/mde-highlight.scss");

  .cm-focused {
    outline: none !important;
  }

  .cm-content {
    font-family: monospace;
    padding: 0;
  }

  .cm-content, .cm-gutter { min-height: 8em; }

  .cm-scroller {
    overflow: hidden;
  }
}
</style>
