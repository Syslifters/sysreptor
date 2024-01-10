<template>
  <div class="mde">
    <markdown-toolbar v-bind="markdownToolbarAttrs" />
    <v-divider />
    <div 
      v-show="props.historic.markdownEditorMode !== MarkdownEditorMode.PREVIEW"
      ref="mergeRef" 
      class="mde-mergeview" 
    />
    
    <v-row v-if="props.historic.markdownEditorMode === MarkdownEditorMode.PREVIEW">
      <v-col cols="6">
        <markdown-preview
          v-bind="markdownPreviewAttrsHistoric" 
          class="mde-preview" 
        />
      </v-col>
      <v-col cols="6">
        <markdown-preview
          v-bind="markdownPreviewAttrsCurrent" 
          class="mde-preview" 
        />
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import type { MarkdownEditorMode } from '#imports';

const props = defineProps<{
  historic: {
    value?: string|null;
    markdownEditorMode?: MarkdownEditorMode;
    rewriteFileUrll?: (fileSrc: string) => string;
    rewriteReferenceLink?: (src: string) => {href: string, title: string}|null;
  },
  current: {
    value?: string|null;
    markdownEditorMode?: MarkdownEditorMode;
    rewriteFileUrll?: (fileSrc: string) => string;
    rewriteReferenceLink?: (src: string) => {href: string, title: string}|null;
  },
}>();

const { markdownPreviewAttrsHistoric, markdownPreviewAttrsCurrent, markdownToolbarAttrs } = useMarkdownDiff({
  props: computed(() => props),
  extensions: markdownEditorDefaultExtensions(),
});
</script>

<style lang="scss" scoped>
$mde-min-height: 15em;

.mde-mergeview {
  width: 100%;
}

:deep(.mde-mergeview) {
  /* set min-height, grow when lines overflow */
  .cm-editor { height: 100%; }
  .cm-content, .cm-gutter { min-height: $mde-min-height; }
  .cm-scroller { overflow: auto; }
  .cm-wrap { border: 1px solid silver; }

  .cm-merge-b {
    border-left: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
  }
}

:deep(.mde-mergeview) {
  @import "@/assets/mde-highlight.scss";
}

.mde-preview {
  min-height: $mde-min-height;
}
</style>
