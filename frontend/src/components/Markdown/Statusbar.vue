<template>
  <div class="mde-statusbar d-flex flex-row">
    <div v-if="props.fileUploadEnabled">
      <span v-if="!props.fileUploadInProgress">Paste or drop to upload files</span>
      <span v-else><v-progress-circular indeterminate :size="16" width="3" class="mr-1"/> Uploading files...</span>
    </div>
    <v-spacer />
    <div class="status-items">
      <span>lines: {{ lineCount }}</span>
      <span>words: {{ wordCount }}</span>
      <span>{{ currentLineNumber }}:{{ currentColNumber }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { EditorState } from 'reportcreator-markdown/editor';

const props = defineProps<{
  editorState: EditorState;
  fileUploadEnabled: boolean;
  fileUploadInProgress: boolean;
}>();

const currentLineNumber = computed(() => props.editorState.doc.lineAt(props.editorState.selection.main.head).number);
const currentColNumber = computed(() => {
  const pos = props.editorState.selection.main.head
  const line = props.editorState.doc.lineAt(pos);
  return pos - line.from;
});
const lineCount = computed(() => props.editorState.doc.lines);
const wordCount = computed(() => {
  const pattern = /[a-zA-Z0-9_\u00A0-\u02AF\u0392-\u03C9\u0410-\u04F9]+|[\u4E00-\u9FFF\u3400-\u4DBF\uF900-\uFAFF\u3040-\u309F\uAC00-\uD7AF]+/g;
  const m = (props.editorState.doc.toString()).match(pattern);
  let count = 0;
  if (!m) { return count; }
  for (let i = 0; i < m.length; i++) {
    if (m[i]!.charCodeAt(0) >= 0x4E00) {
      count += m[i]!.length;
    } else {
      count += 1;
    }
  }
  return count;
});

</script>

<style lang="scss" scoped>
.mde-statusbar {
  width: 100%;
  font-size: smaller;
  padding: 0.3em 1em;
  color: #959694;

  .status-items {
    span {
      display: inline-block;
      min-width: 4em;
      margin-left: 1em;
    }
  }
}
</style>
