<template>
  <v-toolbar dense flat class="toolbar">
    <markdown-toolbar-button @click="toggleStrong" title="Bold" icon="mdi-format-bold" :disabled="disabled" :active="isTypeInSelection('strong')" />
    <markdown-toolbar-button @click="toggleEmphasis" title="Italic" icon="mdi-format-italic" :disabled="disabled" :active="isTypeInSelection('emphasis')" />
    <markdown-toolbar-button @click="toggleStrikethrough" title="Strikethrough" icon="mdi-format-strikethrough" :disabled="disabled" :active="isTypeInSelection('strikethrough')" />
    <span class="separator" />
    <markdown-toolbar-button @click="toggleListUnordered" title="Bullet List" icon="mdi-format-list-bulleted" :disabled="disabled" :active="isTypeInSelection('listUnordered')" />
    <markdown-toolbar-button @click="toggleListOrdered" title="Numbered List" icon="mdi-format-list-numbered" :disabled="disabled" :active="isTypeInSelection('listOrdered')" />
    <markdown-toolbar-button @click="insertCodeBlock" title="Code" icon="mdi-code-tags" :disabled="disabled" :active="isTypeInSelection('codeFenced')" />
    <markdown-toolbar-button @click="insertTable" title="Table" icon="mdi-table" :disabled="disabled" :active="isTypeInSelection('table')" />
    <span class="separator" />
    <markdown-toolbar-button @click="toggleLink" title="Link" icon="mdi-link" :disabled="disabled" :active="isTypeInSelection('link')" />
    <template v-if="uploadFiles">
      <markdown-toolbar-button @click="$refs.fileInput.click()" title="Image" icon="mdi-image" :disabled="disabled || fileUploadInProgress" />
      <input ref="fileInput" type="file" multiple @change="onUploadFiles" :disabled="disabled || fileUploadInProgress" class="d-none" />
    </template>
    <span class="separator" />
    <markdown-toolbar-button @click="spellcheckEnabled = !spellcheckEnabled" title="Spellcheck" icon="mdi-spellcheck" :disabled="disabled || !spellcheckSupported" :active="spellcheckEnabled" />
    <span class="separator" />
    <markdown-toolbar-button @click="undo" title="Undo" icon="mdi-undo" :disabled="disabled || !canUndo" />
    <markdown-toolbar-button @click="redo" title="Redo" icon="mdi-redo" :disabled="disabled || !canRedo" />
    <span class="separator" />
    <markdown-toolbar-button v-if="editorMode === 'markdown'" @click="editorMode = 'markdown-preview'" title="Markdown" icon="mdi-language-markdown" :active="true" />
    <markdown-toolbar-button v-else-if="editorMode === 'markdown-preview'" @click="editorMode = 'preview'" title="Side-by-Side View" icon="mdi-view-split-vertical" :active="true" />
    <markdown-toolbar-button v-else-if="editorMode === 'preview'" @click="editorMode = 'markdown'" title="Preview" icon="mdi-image-filter-hdr" :active="true" />
  </v-toolbar>
</template>

<script>
import { undo, redo, undoDepth, redoDepth } from '@codemirror/commands';
import { isTypeInSelection, toggleStrong, toggleEmphasis, toggleStrikethrough, toggleListUnordered, toggleListOrdered, toggleLink, insertCodeBlock, insertTable } from 'reportcreator-markdown/editor/commands.js';

export default {
  props: {
    editorView: {
      type: Object,
      required: true,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    uploadFiles: {
      type: Function,
      default: null
    },
    fileUploadInProgress: {
      type: Boolean,
      default: false
    },
    lang: {
      type: String,
      default: null,
    },
  },
  computed: {
    editorMode: {
      get() {
        return this.$store.state.settings.markdownEditorMode;
      },
      set(val) {
        this.$store.commit('settings/updateMarkdownEditorMode', val);
      },
    },
    spellcheckSupported() {
      return this.$store.getters['apisettings/settings'].features.spellcheck &&
             this.$store.getters['apisettings/settings'].languages.find(l => l.code === this.lang)?.spellcheck;
    },
    spellcheckEnabled: {
      get() {
        return this.$store.state.settings.spellcheckEnabled && this.spellcheckSupported;
      },
      set(val) {
        this.$store.commit('settings/updateSpellcheckEnabled', val);
      }
    },
    canUndo() {
      if (this.editorView) {
        return undoDepth(this.editorView.state);
      }
      return false;
    },
    canRedo() {
      if (this.editorView) {
        return redoDepth(this.editorView.state);
      }
      return false;
    },
  },
  methods: {
    ...Object.fromEntries(Object.entries({
      undo,
      redo,
      toggleStrong,
      toggleEmphasis,
      toggleStrikethrough,
      toggleListUnordered,
      toggleListOrdered,
      toggleLink,
      insertCodeBlock,
      insertTable,
    })
      .map(([n, fn]) => [n, function() { 
        if (!this.editorView) {
          return false;
        }

        try {
          return fn(this.editorView); 
        } catch (err) {
          // eslint-disable-next-line no-console
          console.error('Error in CodeMirror action', err);
        }
      }])),
    isTypeInSelection(type) {
      if (!this.editorView) {
        return false;
      }
      return isTypeInSelection(this.editorView.state, type);
    },
    async onUploadFiles(event) {
      const files = event.target.files;
      try {
        await this.uploadFiles(files);
      } finally {
        this.$refs.fileInput.value = null;
      }
    },
  }
}
</script>

<style lang="scss" scoped>
.toolbar {
  background-color: inherit !important;
}

.separator {
  display: inline-block;
  height: 1.5em;
  width: 0;
  border-left: 1px solid #d9d9d9;
  border-right: 1px solid #fff;
  color: transparent;
  text-indent: -10px;
  margin: 0 0.5em;
}
</style>
