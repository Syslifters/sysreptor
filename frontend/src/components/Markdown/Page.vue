<template>
  <full-height-page class="mde">
    <template #header>
      <markdown-toolbar v-if="editorView" v-bind="markdownToolbarAttrs" />
      <v-divider />
    </template>

    <template #default>
      <v-row no-gutters class="h-100">
        <v-col :cols="localSettings.markdownEditorMode === MarkdownEditorMode.MARKDOWN_AND_PREVIEW ? 6 : undefined" v-show="localSettings.markdownEditorMode !== MarkdownEditorMode.PREVIEW" class="h-100">
          <div
            ref="editorRef"
            class="mde-editor h-100 overflow-y-auto"
            :class="{'mde-editor-side': localSettings.markdownEditorMode === MarkdownEditorMode.MARKDOWN_AND_PREVIEW}"
          />
        </v-col>
        <v-col v-if="localSettings.markdownEditorMode === MarkdownEditorMode.MARKDOWN_AND_PREVIEW" class="h-100">
          <v-divider vertical class="h-100" />
        </v-col>
        <v-col :cols="localSettings.markdownEditorMode === MarkdownEditorMode.MARKDOWN_AND_PREVIEW ? 6 : undefined" v-if="localSettings.markdownEditorMode !== MarkdownEditorMode.MARKDOWN" class="h-100">
          <markdown-preview v-bind="markdownPreviewAttrs" class="preview h-100 overflow-y-auto" />
        </v-col>
      </v-row>
    </template>
  </full-height-page>
</template>

<script setup lang="ts">
import { markdownEditorPageExtensions } from "~/composables/markdown";

const localSettings = useLocalSettings();

const props = defineProps(makeMarkdownProps({
  files: true,
  spellcheckSupportedDefault: true,
}));
const emit = defineEmits(makeMarkdownEmits());

const { editorView, markdownToolbarAttrs, markdownPreviewAttrs, focus, blur } = useMarkdownEditor({
  props: computed(() => ({ ...props, spellcheckSupported: true })),
  emit,
  extensions: markdownEditorPageExtensions(),
});

defineExpose({
  focus,
  blur,
});
</script>

<style lang="scss" scoped>
.mde-editor-side.cm-editor {
  width: 50%;
}

:deep(.mde-editor) {
  .cm-editor {
    height: 100%;
  }
}

:deep(.mde-editor) {
  @import "@/assets/mde-highlight.scss";

  .cm-content {
    font-family: monospace;
  }
}

.preview {
  height: 100%;
  padding: 0.5em;

  &-side {
    width: 50%;
  }
}
</style>
