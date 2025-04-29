<template>
  <div class="mde">
    <markdown-toolbar ref="toolbarRef" v-bind="markdownToolbarAttrs" />
    <teleport v-if="toolbarRef && $slots['context-menu']" :to="`#${toolbarRef!.additionalContentId}`" defer>
      <!-- 
        Context menu for the markdown-toolbar.
        Use teleport instead of slots to improve render performance.
        When slots are defined inside <markdown-toolbar> drastically increase render time, even when not actually rendered (behind a v-if).
      -->
      <markdown-toolbar-context-menu>
        <template #default><slot name="context-menu" :disabled="markdownToolbarAttrs.disabled" /></template>
      </markdown-toolbar-context-menu>
    </teleport>

    <v-row no-gutters class="w-100">
      <v-col 
        v-show="props.markdownEditorMode !== MarkdownEditorMode.PREVIEW"
        :cols="props.markdownEditorMode === MarkdownEditorMode.MARKDOWN_AND_PREVIEW ? 6 : undefined"
      >
        <div
          ref="editorRef"
          v-intersect="onIntersect"
          class="mde-editor"
        />
      </v-col>
      <v-col 
        v-if="props.markdownEditorMode === MarkdownEditorMode.MARKDOWN_AND_PREVIEW" 
        class="w-0"
      >
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
import { MarkdownEditorMode } from '#imports';

const props = defineProps(makeMarkdownProps());
const emit = defineEmits(makeMarkdownEmits());

const { editorView, markdownToolbarAttrs, markdownStatusbarAttrs, markdownPreviewAttrs, onIntersect, focus, blur } = useMarkdownEditor({
  props: computed(() => ({ ...props, spellcheckSupported: true } as any)),
  emit,
  extensions: markdownEditorDefaultExtensions(),
  fileUploadSupported: true,
});

const toolbarRef = useTemplateRef('toolbarRef');

defineExpose({
  focus,
  blur,
});
</script>

<style lang="scss" scoped>
@use "sass:meta";

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
  @include meta.load-css("@/assets/mde-highlight.scss");
}

.mde-preview {
  min-height: $mde-min-height;
}
</style>
