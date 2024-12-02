<template>
  <v-toolbar ref="toolbarRef" density="compact" flat class="toolbar">
    <markdown-toolbar-button @click="codemirrorAction(toggleStrong)" title="Bold (Ctrl+B)" icon="mdi-format-bold" :disabled="props.disabled" :active="isTypeInSelection(props.editorState, 'strong')" />
    <markdown-toolbar-button @click="codemirrorAction(toggleEmphasis)" title="Italic (Ctrl+I)" icon="mdi-format-italic" :disabled="props.disabled" :active="isTypeInSelection(props.editorState, 'emphasis')" />
    <markdown-toolbar-button @click="codemirrorAction(toggleStrikethrough)" title="Strikethrough" icon="mdi-format-strikethrough" :disabled="props.disabled" :active="isTypeInSelection(props.editorState, 'strikethrough')" />
    <markdown-toolbar-button @click="codemirrorAction(toggleFootnote)" title="Footnote" icon="mdi-format-superscript" :disabled="props.disabled" :active="isTypeInSelection(props.editorState, 'inlineFootnote')" />
    <span class="separator" />
    <markdown-toolbar-button @click="codemirrorAction(toggleListUnordered)" title="Bullet List" icon="mdi-format-list-bulleted" :disabled="props.disabled" :active="isTypeInSelection(props.editorState, 'listUnordered')" />
    <markdown-toolbar-button @click="codemirrorAction(toggleListOrdered)" title="Numbered List" icon="mdi-format-list-numbered" :disabled="props.disabled" :active="isTypeInSelection(props.editorState, 'listOrdered')" />
    <markdown-toolbar-button @click="codemirrorAction(toggleTaskList)" title="Checklist" icon="mdi-format-list-checkbox" :disabled="props.disabled" :active="isTaskListInSelection(props.editorState)" />
    <markdown-toolbar-button @click="codemirrorAction(insertCodeBlock)" title="Code" icon="mdi-code-tags" :disabled="props.disabled" :active="isTypeInSelection(props.editorState, 'codeFenced')" />
    <markdown-toolbar-button @click="codemirrorAction(insertTable)" title="Table" icon="mdi-table" :disabled="props.disabled" :active="isTypeInSelection(props.editorState, 'table')" />
    <span class="separator" />
    <v-menu
      v-if="props.referenceItems"
      :disabled="props.disabled || props.referenceItems.length === 0"
    >
      <template #activator="{ props: menuProps }">
        <markdown-toolbar-button title="Finding Reference" icon="mdi-alpha-f-box-outline" v-bind="menuProps" />
      </template>
      <template #default>
        <v-list density="compact" class="pa-0 finding-reference-list">
          <v-list-subheader>Finding Reference</v-list-subheader>
          <v-list-item
            v-for="item in props.referenceItems"
            :key="item.id"
            @click="codemirrorAction(() => insertText(props.editorView!, `[](#${item.id})`))"
            :title="item.title"
            :class="'finding-level-' + levelNumberFromLevelName(item.severity)"
          />
        </v-list>
      </template>
    </v-menu>
    <markdown-toolbar-button @click="codemirrorAction(toggleLink)" title="Link" icon="mdi-link" :disabled="props.disabled" :active="isTypeInSelection(props.editorState, 'link')" />
    <template v-if="uploadFiles">
      <markdown-toolbar-button @click="fileInput.click()" title="Image" icon="mdi-image" :disabled="props.disabled || props.fileUploadInProgress" />
      <input ref="fileInput" type="file" multiple @change="e => onUploadFiles(e as InputEvent)" @click.stop :disabled="props.disabled || props.fileUploadInProgress" class="d-none" />
    </template>
    <span class="separator" />
    <markdown-toolbar-button @click="codemirrorAction(undo)" title="Undo" icon="mdi-undo" :disabled="props.disabled || !canUndo" />
    <markdown-toolbar-button @click="codemirrorAction(redo)" title="Redo" icon="mdi-redo" :disabled="props.disabled || !canRedo" />
    <span class="separator" />
    <template v-if="props.spellcheckSupported || props.collab?.comments">
      <markdown-toolbar-button
        v-if="props.spellcheckSupported && apiSettings.isProfessionalLicense"
        @click="toggleSpellcheck"
        title="Spell check"
        icon="mdi-spellcheck"
        :disabled="props.disabled || !spellcheckSupported"
        :active="spellcheckEnabled"
      />
      <markdown-toolbar-button
        v-else-if="props.spellcheckSupported"
        @click="toggleSpellcheck"
        :title="'Spell check (basic)'"
        icon="mdi-spellcheck"
        :dot="!spellcheckSupported ? undefined : (spellcheckEnabled ? 'warning' : 'error')"
        :disabled="props.disabled || !spellcheckSupported"
        :active="spellcheckEnabled"
      />
      <markdown-toolbar-button
        v-if="props.collab?.comments"
        @click="emitCreateComment"
        title="Comment (Ctrl+Alt+M)"
        icon="mdi-comment-plus-outline"
        :disabled="props.disabled || !props.editorState"
      />
      <span class="separator" />
    </template>
    <s-btn-icon 
      v-if="slots['context-menu']"
      size="small"
      density="comfortable"
    >
      <v-icon icon="mdi-dots-vertical" />
      <v-tooltip activator="parent" location="top" text="More actions" />

      <v-menu activator="parent">
        <template #default>
          <v-list density="compact">
            <slot 
              name="context-menu" 
              :disabled="props.disabled"
            />
          </v-list>
        </template>
      </v-menu>
    </s-btn-icon>

    <v-spacer />
    <markdown-toolbar-button v-if="props.markdownEditorMode === MarkdownEditorMode.MARKDOWN" @click="setMarkdownEditorMode(MarkdownEditorMode.MARKDOWN_AND_PREVIEW)" title="Markdown" icon="mdi-language-markdown" :active="true" />
    <markdown-toolbar-button v-else-if="props.markdownEditorMode === MarkdownEditorMode.MARKDOWN_AND_PREVIEW" @click="setMarkdownEditorMode(MarkdownEditorMode.PREVIEW)" title="Side-by-Side View" icon="mdi-view-split-vertical" :active="true" />
    <markdown-toolbar-button v-else-if="props.markdownEditorMode === MarkdownEditorMode.PREVIEW" @click="setMarkdownEditorMode(MarkdownEditorMode.MARKDOWN)" title="Preview" icon="mdi-image-filter-hdr" :active="true" />
  </v-toolbar>
</template>

<script setup lang="ts">
import {
  type EditorView,
  type EditorState,
  insertCodeBlock,
  insertTable,
  insertText,
  redo,
  redoDepth,
  toggleEmphasis,
  toggleLink,
  toggleListOrdered,
  toggleListUnordered,
  toggleTaskList,
  toggleStrikethrough,
  toggleStrong,
  toggleFootnote,
  undo,
  undoDepth,
  isTypeInSelection,
  isTaskListInSelection,
} from '@sysreptor/markdown/editor';
import type { VToolbar } from 'vuetify/lib/components/index.mjs';
import { levelNumberFromLevelName } from '@base/utils/cvss';
import { MarkdownEditorMode, type ReferenceItem } from '#imports';

const props = defineProps<{
  editorView?: EditorView|null;
  editorState?: EditorState|null;
  spellcheckSupported?: boolean;
  spellcheckEnabled?: boolean;
  markdownEditorMode?: MarkdownEditorMode;
  referenceItems?: ReferenceItem[];
  disabled?: boolean;
  lang?: string|null;
  collab?: CollabPropType;
  uploadFiles?: (files: FileList) => Promise<void>;
  fileUploadInProgress?: boolean;
}>();
const emit = defineEmits<{
  'update:spellcheckEnabled': [value: boolean];
  'update:markdownEditorMode': [value: MarkdownEditorMode];
  'comment': [value: any];
}>();

const apiSettings = useApiSettings();
const slots = useSlots();

const spellcheckSupported = computed(() => {
  if (!props.spellcheckSupported) {
    return false
  }

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

function emitCreateComment() {
  if (!props.collab?.comments || !props.editorState || props.disabled) {
    return;
  }
  
  const selectionRange = props.editorState.selection.main
  emit('comment', {
    type: 'create', 
    comment: { 
      text: '', 
      collabPath: props.collab.path, 
      text_range: selectionRange.empty ? null : { from: selectionRange.from, to: selectionRange.to },
    }
  })
}

</script>

<style lang="scss" scoped>
@use 'sass:map';
@use "@base/assets/settings" as settings;

@for $level from 1 through 5 {
  .finding-level-#{$level} {
    border-left: 0.4em solid map.get(settings.$risk-color-levels, $level);
  }
}

.toolbar {
  background-color: rgba(var(--v-theme-surface), 1) !important;
  border-bottom: thin solid rgba(var(--v-theme-on-surface), var(--v-border-opacity));
  position: sticky;
  top: 0;
  z-index: 1;
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

.finding-reference-list {
  max-height: 70vh;
}
</style>
