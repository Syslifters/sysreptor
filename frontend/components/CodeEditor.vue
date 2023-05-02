<template>
  <div ref="editor"></div>
</template>

<script>
// // Enable features
// import 'monaco-editor/esm/vs/editor/contrib/bracketMatching/browser/bracketMatching';
// import 'monaco-editor/esm/vs/editor/contrib/comment/browser/comment';
// import 'monaco-editor/esm/vs/editor/contrib/cursorUndo/browser/cursorUndo'
// import 'monaco-editor/esm/vs/editor/contrib/find/browser/findController'
// import 'monaco-editor/esm/vs/editor/contrib/folding/browser/folding';
// import 'monaco-editor/esm/vs/editor/contrib/indentation/browser/indentation'
// // import 'monaco-editor/esm/vs/editor/contrib/inlineCompletions/browser/';
// import 'monaco-editor/esm/vs/editor/contrib/linesOperations/browser/linesOperations'
// import 'monaco-editor/esm/vs/editor/contrib/parameterHints/browser/parameterHints'
// import 'monaco-editor/esm/vs/editor/contrib/rename/browser/rename'
// import 'monaco-editor/esm/vs/editor/contrib/smartSelect/browser/smartSelect'
// import 'monaco-editor/esm/vs/editor/contrib/suggest/browser/suggest'
// import 'monaco-editor/esm/vs/editor/contrib/wordHighlighter/browser/wordHighlighter'
// // import 'monaco-editor/esm/vs/editor/browser/controller/coreCommands.js';

// // // Enable languages
// import 'monaco-editor/esm/vs/language/html/monaco.contribution'
// import 'monaco-editor/esm/vs/language/css/monaco.contribution'

// import * as monaco from 'monaco-editor/esm/vs/editor/editor.api';

import * as monaco from 'monaco-editor';

export default {
  props: {
    value: {
      type: String,
      required: true,
    },
    language: {
      type: String,
      default: null,
    },
    disabled: {
      type: Boolean,
      default: false,
    }
  },
  emits: ['input'],
  data() {
    return {
      editor: null,
    }
  },
  watch: {
    value(newVal) {
      if (this.editor && newVal !== this.editor.getValue()) {
        this.editor.setValue(newVal);
      }
    },
    disabled(newVal) {
      if (this.editor) {
        this.editor.updateOptions({ readOnly: newVal });
      }
    }
  },
  mounted() {
    // https://microsoft.github.io/monaco-editor/api/interfaces/monaco.editor.IStandaloneEditorConstructionOptions.html
    this.editor = monaco.editor.create(this.$refs.editor, {
      value: this.value,
      language: this.language,
      readOnly: this.disabled,
      theme: 'vs',
      minimap: {
        enabled: false,
      },
      contextmenu: false,
      codeLens: false,
      folding: true,
      lightbulb: false,
      automaticLayout: true,
      wordWrap: 'on',
      fixedOverflowWidgets: true,
    });
    this.editor.onDidChangeModelContent((event) => {
      this.$emit('input', this.editor.getValue());
    });
  },
  beforeDestroy() {
    if (this.editor) {
      this.editor.dispose();
    }
  }
  
}
</script>
