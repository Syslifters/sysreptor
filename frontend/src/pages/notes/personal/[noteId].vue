<template>
  <full-height-page v-if="note" :key="note.id">
    <template #header>
      <edit-toolbar v-bind="toolbarAttrs">
        <template #title>
          <div class="note-title-container">
            <div>
              <s-btn-icon
                @click="updateKey('checked', note.checked === null ? false : !note.checked ? true : null)"
                :icon="note.checked === null ? 'mdi-checkbox-blank-off-outline' : note.checked ? 'mdi-checkbox-marked' : 'mdi-checkbox-blank-outline'"
                :disabled="notesCollab.readonly.value"
                density="comfortable"
              />
            </div>
            <s-emoji-picker-field
              v-if="note.checked === null"
              :model-value="note.icon_emoji"
              @update:model-value="updateKey('icon_emoji', $event)"
              :empty-icon="hasChildNotes ? 'mdi-folder-outline' : 'mdi-note-text-outline'"
              :readonly="notesCollab.readonly.value"
              density="comfortable"
            />
              
            <markdown-text-field-content
              ref="titleRef"
              :model-value="note.title"
              :collab="collabSubpath(notesCollab.collabProps.value, 'title')"
              @collab="notesCollab.onCollabEvent"
              v-bind="inputFieldAttrs"
              class="note-title"
            />
          </div>
        </template>
        <template #context-menu>
          <btn-export
            :export-url="exportUrl"
            :name="'notes-' + note.title"
          />
          <btn-export
            :export-url="exportPdfUrl"
            :name="note.title"
            extension=".pdf"
            button-text="Export as PDF"
          />
        </template>
      </edit-toolbar>
    </template>
    <template #default>
      <markdown-page
        ref="textRef"
        :model-value="note.text"
        :collab="collabSubpath(notesCollab.collabProps.value, 'text')"
        @collab="notesCollab.onCollabEvent"
        v-bind="inputFieldAttrs"
      />
    </template>
  </full-height-page>
</template>

<script setup lang="ts">
import urlJoin from "url-join";
import { MarkdownEditorMode } from "~/utils/types";
import { uploadFileHelper } from "~/utils/upload";

const route = useRoute();
const localSettings = useLocalSettings();
const userNotesStore = useUserNotesStore();

const notesCollab = userNotesStore.useNotesCollab({ noteId: route.params.noteId as string });
const note = computed(() => notesCollab.data.value.notes[route.params.noteId as string]);

const toolbarAttrs = computed(() => ({
  data: note.value,
  delete: async (note: ProjectNote) => {
    await userNotesStore.deleteNote(note);
    await navigateTo('/notes/personal/');
  },
}));

function updateKey(key: string, value: any) {
  notesCollab.onCollabEvent({
    type: CollabEventType.UPDATE_KEY,
    path: collabSubpath(notesCollab.collabProps.value, key).path,
    value,
  })
}

const baseUrl = computed(() => `/api/v1/pentestusers/self/notes/${route.params.noteId}/`);
const exportUrl = computed(() => urlJoin(baseUrl.value, '/export/'));
const exportPdfUrl = computed(() => urlJoin(baseUrl.value, '/export-pdf/'));
const hasChildNotes = computed(() => {
  if (!note.value) {
    return false;
  }
  return userNotesStore.notes
    .some(n => n.parent === note.value!.id && n.id !== note.value!.id);
});

async function uploadFile(file: File) {
  const obj = await uploadFileHelper<UploadedFileInfo>('/api/v1/pentestusers/self/notes/upload/', file);
  if (obj.resource_type === 'file') {
    return `[${obj.name}](/files/name/${obj.name})`;
  } else {
    return `![${obj.name}](/images/name/${obj.name}){width="auto"}`;
  }
}
function rewriteFileUrl(imgSrc: string) {
  return urlJoin('/api/v1/pentestusers/self/notes/', imgSrc);
}
const inputFieldAttrs = computed(() => ({
  readonly: notesCollab.readonly.value,
  lang: 'auto',
  spellcheckSupported: true,
  spellcheckEnabled: localSettings.userNoteSpellcheckEnabled,
  'onUpdate:spellcheckEnabled': (val: boolean) => { localSettings.userNoteSpellcheckEnabled = val }, 
  markdownEditorMode: localSettings.userNoteMarkdownEditorMode,
  'onUpdate:markdownEditorMode': (val: MarkdownEditorMode) => { localSettings.userNoteMarkdownEditorMode = val },
  uploadFile,
  rewriteFileUrl,
}));

// Autofocus input
const titleRef = ref();
const textRef = ref();
watch(note, async (note) => {
  if (note) {
    await nextTick();
    if (route.query?.focus === 'title') {
      titleRef.value?.focus();
    } else {
      textRef.value?.focus();
    }
  }
}, { immediate: true });
</script>

<style lang="scss" scoped>
.note-title-container {
  display: flex;
  flex-direction: row;
  align-items: center;
  
  & > * {
    flex-shrink: 0;
  }

  .note-title {
    flex-grow: 1;
    flex-shrink: 1;
    min-width: 0;
    margin-left: 0.25em;
    margin-right: 0.25em;
  }
}
</style>
