<template>
  <v-toolbar density="compact" flat class="toolbar">
    <markdown-toolbar-button @click="codemirrorAction(toggleStrong)" title="Bold" icon="mdi-format-bold" :disabled="props.disabled" :active="isTypeInSelection(props.editorState, 'strong')" />
    <markdown-toolbar-button @click="codemirrorAction(toggleEmphasis)" title="Italic" icon="mdi-format-italic" :disabled="props.disabled" :active="isTypeInSelection(props.editorState, 'emphasis')" />
    <markdown-toolbar-button @click="codemirrorAction(toggleStrikethrough)" title="Strikethrough" icon="mdi-format-strikethrough" :disabled="props.disabled" :active="isTypeInSelection(props.editorState, 'strikethrough')" />
    <span class="separator" />
    <markdown-toolbar-button @click="codemirrorAction(toggleListUnordered)" title="Bullet List" icon="mdi-format-list-bulleted" :disabled="props.disabled" :active="isTypeInSelection(props.editorState, 'listUnordered')" />
    <markdown-toolbar-button @click="codemirrorAction(toggleListOrdered)" title="Numbered List" icon="mdi-format-list-numbered" :disabled="props.disabled" :active="isTypeInSelection(props.editorState, 'listOrdered')" />
    <markdown-toolbar-button @click="codemirrorAction(insertCodeBlock)" title="Code" icon="mdi-code-tags" :disabled="props.disabled" :active="isTypeInSelection(props.editorState, 'codeFenced')" />
    <markdown-toolbar-button @click="codemirrorAction(insertTable)" title="Table" icon="mdi-table" :disabled="props.disabled" :active="isTypeInSelection(props.editorState, 'table')" />
    <span class="separator" />
    <markdown-toolbar-button @click="codemirrorAction(toggleLink)" title="Link" icon="mdi-link" :disabled="props.disabled" :active="isTypeInSelection(props.editorState, 'link')" />
    <template v-if="uploadFiles">
      <markdown-toolbar-button @click="fileInput.click()" title="Image" icon="mdi-image" :disabled="props.disabled || props.fileUploadInProgress" />
      <input ref="fileInput" type="file" multiple @change="onUploadFiles" @click.stop :disabled="props.disabled || props.fileUploadInProgress" class="d-none" />
    </template>
    <span class="separator" />
    <markdown-toolbar-button
      v-if="apiSettings.isProfessionalLicense"
      @click="spellcheckEnabled = !spellcheckEnabled"
      title="Spellcheck"
      icon="mdi-spellcheck"
      :disabled="props.disabled || !spellcheckSupported"
      :active="spellcheckEnabled"
    />
    <markdown-toolbar-button
      v-else
      @click="toggleBrowserSpellcheckCommunity"
      :title="'Spellcheck (browser-based)'"
      icon="mdi-spellcheck"
      :dot="!spellcheckSupported ? undefined : (spellcheckEnabled ? 'warning' : 'error')"
      :disabled="props.disabled || !spellcheckSupported"
      :active="spellcheckEnabled"
    />
    <span class="separator" />
    <markdown-toolbar-button @click="codemirrorAction(undo)" title="Undo" icon="mdi-undo" :disabled="props.disabled || !canUndo" />
    <markdown-toolbar-button @click="codemirrorAction(redo)" title="Redo" icon="mdi-redo" :disabled="props.disabled || !canRedo" />
    <span class="separator" />
    <v-spacer />
    <markdown-toolbar-button v-if="localSettings.markdownEditorMode === MarkdownEditorMode.MARKDOWN" @click="localSettings.markdownEditorMode = MarkdownEditorMode.MARKDOWN_AND_PREVIEW" title="Markdown" icon="mdi-language-markdown" :active="true" />
    <markdown-toolbar-button v-else-if="localSettings.markdownEditorMode === MarkdownEditorMode.MARKDOWN_AND_PREVIEW" @click="localSettings.markdownEditorMode = MarkdownEditorMode.PREVIEW" title="Side-by-Side View" icon="mdi-view-split-vertical" :active="true" />
    <markdown-toolbar-button v-else-if="localSettings.markdownEditorMode === MarkdownEditorMode.PREVIEW" @click="localSettings.markdownEditorMode = MarkdownEditorMode.MARKDOWN" title="Preview" icon="mdi-image-filter-hdr" :active="true" />
  </v-toolbar>
</template>

<script setup lang="ts">
// @ts-ignore
import {
  EditorView,
  EditorState,
  insertCodeBlock,
  insertTable,
  redo,
  redoDepth,
  toggleEmphasis,
  toggleLink,
  toggleListOrdered,
  toggleListUnordered,
  toggleStrikethrough,
  toggleStrong,
  undo,
  undoDepth,
  isTypeInSelection,
  // @ts-ignore
} from 'reportcreator-markdown/editor';

const props = defineProps<{
  editorView: EditorView;
  editorState: EditorState;
  disabled?: boolean;
  lang?: string;
  uploadFiles?: (files: FileList) => Promise<void>;
  fileUploadInProgress?: boolean;
}>();

const localSettings = useLocalSettings();
const apiSettings = useApiSettings();

const spellcheckSupported = computed(() => {
  if (apiSettings.isProfessionalLicense) {
    return apiSettings.spellcheckLanguageToolSupported;
  } else {
    return Boolean(props.lang);
  }
});
const spellcheckEnabled = computed({
  get: () => localSettings.spellcheckEnabled && spellcheckSupported.value,
  set: (val) => { localSettings.spellcheckEnabled = val },
});
function toggleBrowserSpellcheckCommunity() {
  spellcheckEnabled.value = !spellcheckEnabled.value;
  if (spellcheckEnabled.value) {
    warningToast('Enabled browser-based spellcheck. Upgrade to Professional for built-in spellchecking.');
  }
}

const canUndo = computed(() => undoDepth(props.editorState) > 0);
const canRedo = computed(() => redoDepth(props.editorState) > 0);

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

function codemirrorAction(actionFn: (view: EditorView) => void) {
  try {
    return actionFn(props.editorView);
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error('Error in CodeMirror action', err);
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
