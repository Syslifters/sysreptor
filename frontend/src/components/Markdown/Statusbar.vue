<template>
  <div class="mde-statusbar">
    <template v-if="props.fileUploadEnabled">
      <span v-if="!props.fileUploadInProgress">Attach files via drag and drop or pasting from clipboard.</span>
      <span v-else>Upload in progress...</span>
    </template>
    <span>lines: {{ lineCount }}</span>
    <span>words: {{ wordCount }}</span>
    <span>{{ currentLineNumber }}:{{ currentColNumber }}</span>
  </div>
</template>

<script setup lang="ts">
import { EditorState } from 'reportcreator-markdown/editor';

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
