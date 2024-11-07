<template>
  <full-height-page class="mde">
    <template #header>
      <markdown-toolbar v-bind="markdownToolbarAttrs" />
    </template>

    <template #default>
      <div 
        v-show="props.historic.markdownEditorMode !== MarkdownEditorMode.PREVIEW"
        ref="mergeViewRef"
        class="mde-mergeview w-100 h-100 overflow-y-auto"
      />

      <v-row 
        v-if="props.historic.markdownEditorMode === MarkdownEditorMode.PREVIEW" 
        no-gutters 
        class="w-100 h-100"
      >
        <v-col cols="6" class="h-100">
          <markdown-preview v-bind="markdownPreviewAttrsHistoric" />
        </v-col>
        <v-col class="h-100 w-0">
          <v-divider vertical class="h-100" />
        </v-col>
        <v-col cols="6" class="h-100">
          <markdown-preview v-bind="markdownPreviewAttrsCurrent" />
        </v-col>
      </v-row>
    </template>
  </full-height-page>
</template>

<script setup lang="ts">
import { MarkdownEditorMode } from '#imports';

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

:deep(.mde-mergeview) {
  .cm-wrap { border: 1px solid silver; }

  .cm-merge-a, .cm-merge-b {
    border-left: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
  }
}

:deep(.mde-mergeview) {
  @include meta.load-css("@/assets/mde-highlight.scss");

  .cm-content {
    font-family: monospace;
  }
}
</style>
