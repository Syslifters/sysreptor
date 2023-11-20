<template>
  <div class="mde">
    <markdown-toolbar v-if="editorView" v-bind="markdownToolbarAttrs" />
    <v-divider />

    <v-row no-gutters class="w-100">
      <v-col :cols="localSettings.markdownEditorMode === MarkdownEditorMode.MARKDOWN_AND_PREVIEW ? 6 : undefined" v-show="localSettings.markdownEditorMode !== MarkdownEditorMode.PREVIEW">
        <div
          ref="editorRef"
          class="mde-editor"
          :class="{'mde-editor-side': localSettings.markdownEditorMode === MarkdownEditorMode.MARKDOWN_AND_PREVIEW}"
        />
      </v-col>
      <v-col v-if="localSettings.markdownEditorMode === MarkdownEditorMode.MARKDOWN_AND_PREVIEW">
        <v-divider vertical class="h-100" />
      </v-col>
      <v-col :cols="localSettings.markdownEditorMode === MarkdownEditorMode.MARKDOWN_AND_PREVIEW ? 6 : undefined" v-if="localSettings.markdownEditorMode !== MarkdownEditorMode.MARKDOWN">
        <markdown-preview v-bind="markdownPreviewAttrs" class="preview" />
      </v-col>
    </v-row>
    <v-divider />

    <markdown-statusbar v-if="editorView" v-bind="markdownStatusbarAttrs" />
  </div>
</template>

<script setup lang="ts">
const localSettings = useLocalSettings();

const props = defineProps(makeMarkdownProps({
  files: true,
  spellcheckSupportedDefault: true,
}));
const emit = defineEmits(makeMarkdownEmits());

const { editorView, markdownToolbarAttrs, markdownStatusbarAttrs, markdownPreviewAttrs, focus, blur } = useMarkdownEditor({
  props: computed(() => ({ ...props, spellcheckSupported: true })),
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
  display: contents;

  &-side.cm-editor {
    width: 50%;
  }
}

:deep(.mde-editor) {
  /* set min-height, grow when lines overflow */
  .cm-content, .cm-gutter { min-height: $mde-min-height; }
  .cm-scroller { overflow: auto; }
  .cm-wrap { border: 1px solid silver }
}

:deep(.mde-editor) {
  @import "@/assets/mde-highlight.scss";
}

.preview {
  height: 100%;
  min-height: $mde-min-height;
  padding: 0.5em;

  &-side {
    width: 50%;
  }
}
</style>
