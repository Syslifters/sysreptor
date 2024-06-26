<template>
  <div class="mde">
    <markdown-toolbar v-bind="markdownToolbarAttrs" />
    <div 
      v-show="props.historic.markdownEditorMode !== MarkdownEditorMode.PREVIEW"
      ref="mergeViewRef" 
      class="mde-mergeview" 
    />
    
    <v-row 
      v-if="props.historic.markdownEditorMode === MarkdownEditorMode.PREVIEW" 
      no-gutters 
      class="w-100"
    >
      <v-col cols="6">
        <markdown-preview
          v-bind="markdownPreviewAttrsHistoric" 
          class="mde-preview" 
        />
      </v-col>
      <v-col class="w-0">
        <v-divider vertical class="h-100" />
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
import type { DiffFieldProps, MarkdownEditorMode } from '#imports';

const props = defineProps<{
  historic: DiffFieldProps,
  current: DiffFieldProps,
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

  .cm-merge-a, .cm-merge-b {
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
