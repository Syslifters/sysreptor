<template>
  <div class="mde-statusbar d-flex flex-row">
    <div v-if="props.uploadFiles">
      <v-btn 
         v-if="!props.fileUploadInProgress"
        @click="fileInput.click()"
        text="Paste, drop or click to upload files"
        :disabled="props.disabled"
        variant="plain"
        class="btn-upload"
      />
      <span v-else><v-progress-circular indeterminate :size="16" width="3" class="mr-1"/> Uploading files...</span>
      <input ref="fileInput" type="file" multiple @change="e => onUploadFiles(e as InputEvent)" @click.stop :disabled="props.disabled || props.fileUploadInProgress" class="d-none" />
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
import type { EditorState } from '@sysreptor/markdown/editor';

const props = defineProps<{
  editorState: EditorState;
  uploadFiles?: (files: FileList) => Promise<void>;
  fileUploadInProgress?: boolean;
  disabled?: boolean;
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

const fileInput = ref();
async function onUploadFiles(event: InputEvent) {
  const files = (event.target as HTMLInputElement).files;
  if (!files || !props.uploadFiles) { return; }
  try {
    await props.uploadFiles(files);
  } finally {
    if (fileInput.value) {
      fileInput.value.value = null;
    }
  }
}

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

.btn-upload {
  font-size: inherit;
  font-weight: inherit;
  text-transform: inherit;
  letter-spacing: inherit;
  height: unset;
  padding: 0;
}
</style>
