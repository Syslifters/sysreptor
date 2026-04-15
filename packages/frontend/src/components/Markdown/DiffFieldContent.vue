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
      @open-image-dialog="openHistoricImageDialog"
      class="mde-preview mde-preview-historic" 
    />
    <v-divider vertical class="mde-separator" />
    <markdown-preview
      v-if="props.historic.markdownEditorMode === MarkdownEditorMode.PREVIEW"
      v-bind="markdownPreviewAttrsCurrent" 
      @open-image-dialog="openCurrentImageDialog"
      class="mde-preview mde-preview-current" 
    />

    <markdown-image-preview-dialog
      ref="historicPreviewDialogRef"
      v-model="historicPreviewImageSrc"
      :images="historicPreviewImagesAll"
      :readonly="true"
    />
    <markdown-image-preview-dialog
      ref="currentPreviewDialogRef"
      v-model="currentPreviewImageSrc"
      :images="currentPreviewImagesAll"
      :readonly="props.current.readonly"
      :upload-file="markdownPreviewAttrsCurrent.uploadFile"
      :rewrite-file-url-map="markdownPreviewAttrsCurrent.rewriteFileUrlMap"
      @image-edited="markdownPreviewAttrsCurrent.onImageEdited"
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

const historicPreviewDialogRef = useTemplateRef('historicPreviewDialogRef');
const historicPreviewImageSrc = ref<PreviewImage|null>(null);
const historicPreviewImagesAll = ref<PreviewImage[]>([]);
function openHistoricImageDialog(e: { selected: PreviewImage; images: PreviewImage[]; editMode?: boolean }) {
  historicPreviewImagesAll.value = e.images;
  historicPreviewDialogRef.value?.open(e.selected, e.editMode);
}

const currentPreviewDialogRef = useTemplateRef('currentPreviewDialogRef');
const currentPreviewImageSrc = ref<PreviewImage|null>(null);
const currentPreviewImagesAll = ref<PreviewImage[]>([]);
function openCurrentImageDialog(e: { selected: PreviewImage; images: PreviewImage[]; editMode?: boolean }) {
  currentPreviewImagesAll.value = e.images;
  currentPreviewDialogRef.value?.open(e.selected, e.editMode);
}
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
    border-left: thin solid color-mix(in srgb, rgb(var(--v-border-color)) calc(var(--v-border-opacity) * 100%), transparent);
  }
}
</style>
