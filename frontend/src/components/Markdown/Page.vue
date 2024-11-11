<template>
  <full-height-page class="mde">
    <template #header>
      <markdown-toolbar v-if="editorView" v-bind="markdownToolbarAttrs" />
    </template>

    <template #default>
      <v-row no-gutters class="w-100 h-100">
        <v-col 
          v-show="props.markdownEditorMode !== MarkdownEditorMode.PREVIEW" 
          :cols="props.markdownEditorMode === MarkdownEditorMode.MARKDOWN_AND_PREVIEW ? 6 : undefined" 
          class="h-100"
        >
          <div
            ref="editorRef"
            v-intersect="onIntersect"
            v-intersect.once="initialScrollTop"
            class="mde-editor h-100 overflow-y-auto"
            :class="{'mde-editor-side': props.markdownEditorMode === MarkdownEditorMode.MARKDOWN_AND_PREVIEW}"
          />
        </v-col>
        <v-col 
          v-if="props.markdownEditorMode === MarkdownEditorMode.MARKDOWN_AND_PREVIEW" 
          class="h-100 w-0"
        >
          <v-divider vertical class="h-100" />
        </v-col>
        <v-col 
          v-if="props.markdownEditorMode !== MarkdownEditorMode.MARKDOWN" 
          :cols="props.markdownEditorMode === MarkdownEditorMode.MARKDOWN_AND_PREVIEW ? 6 : undefined" 
          class="h-100"
        >
          <markdown-preview v-bind="markdownPreviewAttrs" class="h-100 overflow-y-scroll" />
        </v-col>
      </v-row>
    </template>

    <template #footer>
      <v-divider />
      <markdown-statusbar v-if="editorView" v-bind="markdownStatusbarAttrs" />
    </template>
  </full-height-page>
</template>

<script setup lang="ts">
import { MarkdownEditorMode } from '#imports';

const props = defineProps(makeMarkdownProps());
const emit = defineEmits(makeMarkdownEmits());

const { editorView, markdownToolbarAttrs, markdownStatusbarAttrs, markdownPreviewAttrs, onIntersect, focus, blur } = useMarkdownEditor({
  props: computed(() => props),
  emit,
  extensions: markdownEditorPageExtensions(),
  fileUploadSupported: true,
});

function initialScrollTop() {
  if (editorView.value) {
    editorView.value.scrollDOM.scrollTop = 0;
  }
}

defineExpose({
  focus,
  blur,
});
</script>

<style lang="scss" scoped>
@use "sass:meta";

.mde-editor-side.cm-editor {
  width: 50%;
}

:deep(.mde-editor) {
  .cm-editor {
    height: 100%;
  }
}

:deep(.mde-editor) {
  @include meta.load-css("@/assets/mde-highlight.scss");

  .cm-content {
    font-family: monospace;
  }
}
</style>
