<template>
  <v-toolbar ref="toolbarRef" density="compact" flat class="toolbar">
    <template v-if="props.editorView && props.editorState">
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
        <input ref="fileInput" type="file" multiple @change="e => onUploadFiles(e as InputEvent)" @click.stop :disabled="props.disabled || props.fileUploadInProgress" class="d-none" />
      </template>
      <span class="separator" />
      <markdown-toolbar-button
        v-if="apiSettings.isProfessionalLicense"
        @click="toggleSpellcheck"
        title="Spell check"
        icon="mdi-spellcheck"
        :disabled="props.disabled || !spellcheckSupported"
        :active="spellcheckEnabled"
      />
      <markdown-toolbar-button
        v-else
        @click="toggleSpellcheck"
        :title="'Spell check (basic)'"
        icon="mdi-spellcheck"
        :dot="!spellcheckSupported ? undefined : (spellcheckEnabled ? 'warning' : 'error')"
        :disabled="props.disabled || !spellcheckSupported"
        :active="spellcheckEnabled"
      />
      <span class="separator" />
      <markdown-toolbar-button @click="codemirrorAction(undo)" title="Undo" icon="mdi-undo" :disabled="props.disabled || !canUndo" />
      <markdown-toolbar-button @click="codemirrorAction(redo)" title="Redo" icon="mdi-redo" :disabled="props.disabled || !canRedo" />
      <span class="separator" />
    </template>
    <v-spacer />
    <markdown-toolbar-button v-if="props.markdownEditorMode === MarkdownEditorMode.MARKDOWN" @click="setMarkdownEditorMode(MarkdownEditorMode.MARKDOWN_AND_PREVIEW)" title="Markdown" icon="mdi-language-markdown" :active="true" />
    <markdown-toolbar-button v-else-if="props.markdownEditorMode === MarkdownEditorMode.MARKDOWN_AND_PREVIEW" @click="setMarkdownEditorMode(MarkdownEditorMode.PREVIEW)" title="Side-by-Side View" icon="mdi-view-split-vertical" :active="true" />
    <markdown-toolbar-button v-else-if="props.markdownEditorMode === MarkdownEditorMode.PREVIEW" @click="setMarkdownEditorMode(MarkdownEditorMode.MARKDOWN)" title="Preview" icon="mdi-image-filter-hdr" :active="true" />
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
import type { VToolbar } from 'vuetify/lib/components/index.mjs';
import { MarkdownEditorMode } from '@/utils/types';

const props = defineProps<{
  editorView?: EditorView;
  editorState?: EditorState;
  spellcheckEnabled?: boolean;
  markdownEditorMode?: MarkdownEditorMode;
  disabled?: boolean;
  lang?: string;
  uploadFiles?: (files: FileList) => Promise<void>;
  fileUploadInProgress?: boolean;
}>();
const emit = defineEmits<{
  'update:spellcheckEnabled': [value: boolean];
  'update:markdownEditorMode': [value: MarkdownEditorMode];
}>();

const apiSettings = useApiSettings();

const spellcheckSupported = computed(() => {
  if (apiSettings.isProfessionalLicense) {
    return apiSettings.spellcheckLanguageToolSupportedForLanguage(props.lang);
  } else {
    // Browser-based spellcheck
    return Boolean(props.lang);
  }
});
function toggleSpellcheck() {
  const newVal = !props.spellcheckEnabled;
  emit('update:spellcheckEnabled', newVal);
  if (newVal && !apiSettings.isProfessionalLicense) {
    warningToast('Basic spell check enabled. Upgrade to SysReptor Professional for advanced options.');
  }
}

const canUndo = computed(() => props.editorState && undoDepth(props.editorState) > 0);
const canRedo = computed(() => props.editorState && redoDepth(props.editorState) > 0);

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
  if (!props.editorView) { return; }
  try {
    return actionFn(props.editorView);
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error('Error in CodeMirror action', err);
  }
}

const toolbarRef = ref<VToolbar>();
function getScrollParent(node?: HTMLElement|null) {
  if (!node) { return null; }
  if (node.scrollHeight > node.clientHeight) {
    return node;
  } else {
    return getScrollParent(node.parentElement);
  }
}
async function setMarkdownEditorMode(mode: MarkdownEditorMode) {
  const scrollParent = getScrollParent(toolbarRef.value!.$el);
  const { y: prevTop } = toolbarRef.value!.$el.getBoundingClientRect();

  // Update editor mode => changes view and potentially causes layout jump
  emit('update:markdownEditorMode', mode);
  await nextTick();

  // Restore position, such the toolbar is at the same position
  const { y: newTop } = toolbarRef.value!.$el.getBoundingClientRect();
  if (scrollParent) {
    scrollParent.scrollTop += newTop - prevTop;
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
