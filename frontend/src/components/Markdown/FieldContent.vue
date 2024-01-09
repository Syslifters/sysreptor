<template>
  <div class="mde">
    <markdown-toolbar v-if="editorView" v-bind="markdownToolbarAttrs" />
    <v-divider />

    <v-row no-gutters class="w-100">
      <v-col 
        v-show="props.markdownEditorMode !== MarkdownEditorMode.PREVIEW"
        :cols="props.markdownEditorMode === MarkdownEditorMode.MARKDOWN_AND_PREVIEW ? 6 : undefined"
      >
        <div
          ref="editorRef"
          v-intersect="onIntersect"
          class="mde-editor"
          :class="{'mde-editor-side': props.markdownEditorMode === MarkdownEditorMode.MARKDOWN_AND_PREVIEW}"
        />
      </v-col>
      <v-col v-if="props.markdownEditorMode === MarkdownEditorMode.MARKDOWN_AND_PREVIEW">
        <v-divider vertical class="h-100" />
      </v-col>
      <v-col 
        v-if="props.markdownEditorMode !== MarkdownEditorMode.MARKDOWN"
        :cols="props.markdownEditorMode === MarkdownEditorMode.MARKDOWN_AND_PREVIEW ? 6 : undefined" 
      >
        <markdown-preview v-bind="markdownPreviewAttrs" class="mde-preview" />
      </v-col>
    </v-row>
    <v-divider />

    <markdown-statusbar v-if="editorView" v-bind="markdownStatusbarAttrs" />
  </div>
</template>

<script setup lang="ts">
const props = defineProps(makeMarkdownProps({
  files: true,
  spellcheckSupportedDefault: true,
}));
const emit = defineEmits(makeMarkdownEmits());

const { editorView, markdownToolbarAttrs, markdownStatusbarAttrs, markdownPreviewAttrs, onIntersect, focus, blur } = useMarkdownEditor({
  props: computed(() => ({ ...props, spellcheckSupported: true } as any)),
  emit,
  extensions: markdownEditorDefaultExtensions(),
});

defineExpose({
  focus,
  blur,
});
</script>

<style lang="scss" scoped>
$mde-min-height: 15em;

.mde-editor {
  height: 100%;

  &-side.cm-editor {
    width: 50%;
  }
}

:deep(.mde-editor) {
  /* set min-height, grow when lines overflow */
  .cm-editor { height: 100%; }
  .cm-content, .cm-gutter { min-height: $mde-min-height; }
  .cm-scroller { overflow: auto; }
  .cm-wrap { border: 1px solid silver }
}

:deep(.mde-editor) {
  @import "@/assets/mde-highlight.scss";
}

.mde-preview {
  min-height: $mde-min-height;
}
</style>
