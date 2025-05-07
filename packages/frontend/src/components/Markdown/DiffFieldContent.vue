<template>
  <div class="mde" :class="'mde-mode-' + props.historic.markdownEditorMode">
    <markdown-toolbar 
      class="mde-toolbar" 
      v-bind="markdownToolbarAttrs" 
    />
    <div 
      ref="mergeViewRef" 
      class="mde-mergeview" 
    />

    <markdown-preview
      v-if="props.historic.markdownEditorMode === MarkdownEditorMode.PREVIEW"
      v-bind="markdownPreviewAttrsHistoric" 
      class="mde-preview mde-preview-historic" 
    />
    <v-divider vertical class="mde-separator" />
    <markdown-preview
      v-if="props.historic.markdownEditorMode === MarkdownEditorMode.PREVIEW"
      v-bind="markdownPreviewAttrsCurrent" 
      class="mde-preview mde-preview-current" 
    />
  </div>
</template>

<script setup lang="ts">
import { type DiffFieldProps, MarkdownEditorMode } from '#imports';

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
@use "sass:meta";

.mde {
  --mde-min-height: 18em;

  display: grid;
  grid-template-columns: 1fr auto 1fr;
  grid-template-rows: auto 1fr;
  grid-template-areas:
    "toolbar toolbar toolbar"
    "historic separator current";
  gap: 0;
  align-items: start;
  width: 100%;
}

.mde-toolbar { grid-area: toolbar; }
.mde-separator { grid-area: separator; }
.mde-preview-historic { grid-area: historic; }
.mde-preview-current { grid-area: current; }
.mde-mergeview { grid-column: historic / span current; }
.mde-footer { grid-area: footer; }

.mde-mode-markdown {
  .mde-preview {
    display: none;
  }
}
.mde-mode-preview {
  .mde-mergeview {
    display: none;
  }
}

.mde-preview {
  height: max-content;
  min-height: var(--mde-min-height);
}
:deep(.mde-mergeview) {
  @include meta.load-css("@/assets/mde-highlight.scss");

  /* set min-height, grow when lines overflow */
  .cm-editor { height: 100%; }
  .cm-content, .cm-gutter { min-height: var(--mde-min-height); }
  .cm-scroller { overflow: auto; }
  .cm-wrap { border: 1px solid silver; }

  .cm-merge-a, .cm-merge-b {
    border-left: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
  }
}
</style>
