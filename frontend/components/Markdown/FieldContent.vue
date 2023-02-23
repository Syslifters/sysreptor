<template>
  <div class="mde">
    <markdown-toolbar 
      v-if="editorView"
      :editor-view="editorView" 
      :disabled="disabled"
      :upload-files="uploadFile ? uploadFiles : null"
      :file-upload-in-progress="fileUploadInProgress"
    />
    <v-divider />

    <v-row no-gutters>
      <v-col :cols="editorMode === 'markdown-preview' ? 6 : null" v-show="editorMode !== 'preview'">
        <div
          ref="editor" 
          class="mde-editor" 
          :class="{'mde-editor-side': editorMode === 'markdown-preview'}"
        />
      </v-col>
      <v-col v-if="editorMode === 'markdown-preview'">
        <v-divider vertical />
      </v-col>
      <v-col :cols="editorMode === 'markdown-preview' ? 6 : null" v-if="editorMode !== 'markdown'">
        <markdown-preview :value="value" :rewrite-file-url="rewriteFileUrl" class="preview" />
      </v-col>
    </v-row>
    <v-divider />

    <markdown-statusbar 
      v-if="editorView"
      :editor-view="editorView" 
      :image-upload-enabled="!!uploadFile" 
      :file-upload-in-progress="fileUploadInProgress"
    />
  </div>
</template>

<script>
import MarkdownEditorBase from '~/mixins/MarkdownEditorBase';

export default {
  mixins: [MarkdownEditorBase],
}
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
  @import "~/assets/mde-highlight.scss";
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
