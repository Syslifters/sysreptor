<template>
  <div class="mde-statusbar">
    <template v-if="fileUploadEnabled">
      <span v-if="!fileUploadInProgress">Attach files by drag and dropping or pasting from clipboard.</span>
      <span v-else>Upload in progress...</span>
    </template>
    <span>lines: {{ lineCount }}</span>
    <span>words: {{ wordCount }}</span>
    <span>{{ currentLineNumber }}:{{ currentColNumber }}</span>
  </div>
</template>

<script>
export default {
  props: {
    editorView: {
      type: Object,
      required: true,
    },
    fileUploadEnabled: {
      type: Boolean,
      default: false,
    },
    fileUploadInProgress: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    currentLineNumber() {
      return this.editorView.state.doc.lineAt(this.editorView.state.selection.main.head).number;
    },
    currentColNumber() {
      const pos = this.editorView.state.selection.main.head
      const line = this.editorView.state.doc.lineAt(pos);
      return pos - line.from;
    },
    lineCount() {
      return this.editorView.state.doc.lines;
    },
    wordCount() {
      const pattern = /[a-zA-Z0-9_\u00A0-\u02AF\u0392-\u03C9\u0410-\u04F9]+|[\u4E00-\u9FFF\u3400-\u4DBF\uF900-\uFAFF\u3040-\u309F\uAC00-\uD7AF]+/g;
      const m = (this.editorView.state.doc.toString()).match(pattern);
      let count = 0;
      if (m === null) { return count; }
      for (let i = 0; i < m.length; i++) {
        if (m[i].charCodeAt(0) >= 0x4E00) {
          count += m[i].length;
        } else {
          count += 1;
        }
      }
      return count;
    },
  }
}
</script>

<style lang="scss" scoped>
.mde-statusbar {
  font-size: smaller;
  text-align: right;
  padding: 0.3em 1em;
  color: #959694;

  span {
    display: inline-block;
    min-width: 4em;
    margin-left: 1em;
  }
}
</style>
