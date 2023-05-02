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
        <fill-screen-height @resize="resizeEditor">
          <div
            ref="editor" 
            class="mde-editor" 
          />
        </fill-screen-height>
      </v-col>
      <v-col v-if="editorMode === 'markdown-preview'">
        <v-divider vertical />
      </v-col>
      <v-col :cols="editorMode === 'markdown-preview' ? 6 : null" v-if="editorMode !== 'markdown'">
        <fill-screen-height>
          <markdown-preview :value="value" :rewrite-file-url="rewriteFileUrl" class="preview" />
        </fill-screen-height>
      </v-col>
    </v-row>
  </div>
</template>

<script>
import { scrollPastEnd } from '@codemirror/view';
import MarkdownEditorBase from '~/mixins/MarkdownEditorBase.js';

export default {
  mixins: [MarkdownEditorBase],
  methods: {
    additionalCodeMirrorExtensions() {
      return [
        scrollPastEnd(),
      ]
    },
    resizeEditor() {
      // CodeMirror is not initialized correctly when it is loaded inside a component with dynamic height (e.g. FillScreenHeight)
      // This leads to update and rendering errors. The internal viewState and viewport are not updated which results in lines beining not rendered on scroll.
      // Re-initialize CodeMirror when height changes.
      if (!this.editorView) {
        return;
      }
      this.editorView.destroy();
      this.initializeEditorView();
    },
  },
}
</script>

<style lang="scss" scoped>
.mde-editor {
  height: 100%;

  &-side.cm-editor {
    width: 50%;
  }
}

:deep(.mde-editor) {
  .cm-editor { 
    height: 100%; 
  }
}

:deep(.mde-editor) {
  @import "~/assets/mde-highlight.scss";

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
