<template>
  <full-height-page v-if="shareInfo && note" :key="shareInfo.id + note.id">
    <template #header>
      <edit-toolbar v-bind="toolbarAttrs">
        <template #title>
          <div class="note-title-container">
            <div>
              <s-btn-icon
                @click="updateKey('checked', note.checked === null ? false : !note.checked ? true : null)"
                :icon="note.checked === null ? 'mdi-checkbox-blank-off-outline' : note.checked ? 'mdi-checkbox-marked' : 'mdi-checkbox-blank-outline'"
                :disabled="readonly"
                density="comfortable"
              />
            </div>
            <s-emoji-picker-field
              v-if="note.checked === null"
              :model-value="note.icon_emoji"
              @update:model-value="updateKey('icon_emoji', $event)"
              :empty-icon="hasChildNotes ? 'mdi-folder-outline' : note.type === NoteType.EXCALIDRAW ? 'mdi-drawing' : 'mdi-note-text-outline'"
              :readonly="readonly"
              density="comfortable"
            />
              
            <markdown-text-field-content
              id="title"
              :model-value="note.title"
              :collab="collabPropsTitle"
              @collab="notesCollab.onCollabEvent"
              v-bind="inputFieldAttrs"
              class="note-title"
            />
          </div>
        </template>
      </edit-toolbar>
    </template>
    <template #default>
      <markdown-page
        v-if="note.type === NoteType.TEXT"
        id="text"
        :model-value="note.text"
        :collab="collabPropsText"
        @collab="notesCollab.onCollabEvent"
        v-bind="inputFieldAttrs"
      />
      <notes-excalidraw
        v-else-if="note.type === NoteType.EXCALIDRAW"
        :websocket-url="`api/public/ws/shareinfos/${route.params.shareInfoId}/notes/${route.params.noteId}/excalidraw/`"
        :api-url="`api/public/shareinfos/${route.params.shareInfoId}/notes/${route.params.noteId}/excalidraw/`"
        :image-api-base-url="`/api/public/shareinfos/${route.params.shareInfoId}/notes/images/`"
        :readonly="readonly"
      />
    </template>
  </full-height-page>
</template>

<script setup lang="ts">
import { collabSubpath, type MarkdownEditorMode } from '#imports';

definePageMeta({
  auth: false,
});

const route = useRoute();
const localSettings = useLocalSettings();
const shareInfoStore = useShareInfoStore();

const shareInfo = await useAsyncDataE(async () => await shareInfoStore.getById(route.params.shareInfoId as string));    

const notesCollab = shareInfoStore.useNotesCollab({ shareInfo: shareInfo.value!, noteId: route.params.noteId as string });
const note = computed(() => notesCollab.data.value.notes[route.params.noteId as string]);
const readonly = computed(() => notesCollab.readonly.value);
const collabPropsTitle = computed<CollabPropType>((oldValue) => collabSubpath(notesCollab.collabProps.value, 'title', oldValue));
const collabPropsText = computed<CollabPropType>((oldValue) => collabSubpath(notesCollab.collabProps.value, 'text', oldValue));

async function uploadFile(file: File) {
  const obj = await uploadFileHelper<UploadedFileInfo>(`/api/public/shareinfos/${shareInfo.value!.id}/notes/upload/`, file);
  if (obj.resource_type === 'file') {
    return `[${obj.name}](/files/name/${obj.name})`;
  } else {
    return `![${obj.name}](/images/name/${obj.name}){width="auto"}`;
  }
}
const rewriteFileUrlMap = computed(() => ({
  '/images/': `/api/public/shareinfos/${shareInfo.value!.id}/notes/images/`,
  '/files/': `/api/public/shareinfos/${shareInfo.value!.id}/notes/files/`,
}))
const inputFieldAttrs = computed(() => ({
  readonly: readonly.value,
  lang: 'auto',
  spellcheckSupported: false,
  markdownEditorMode: localSettings.sharedNoteMarkdownEditorMode,
  'onUpdate:markdownEditorMode': (val: MarkdownEditorMode) => { localSettings.sharedNoteMarkdownEditorMode = val },
  uploadFile,
  rewriteFileUrlMap: rewriteFileUrlMap.value,
}));
const toolbarAttrs = computed(() => ({
  data: note.value,
  errorMessage: 
    ((shareInfo.value?.permissions_write && !notesCollab.hasLock.value) ? 'This note is locked by another user. Upgrade to SysReptor Professional for lock-free collaborative editing.' : null),
  canDelete: shareInfo.value?.permissions_write && note.value?.id !== shareInfo.value?.note_id,
  delete: async (note: ProjectNote) => {
    await shareInfoStore.deleteNote(shareInfo.value!, note);
    await navigateTo(`/shared/${shareInfo.value!.id}/notes/`);
  },
}));

function updateKey(key: string, value: any) {
  notesCollab.onCollabEvent({
    type: CollabEventType.UPDATE_KEY,
    path: collabSubpath(notesCollab.collabProps.value, key).path,
    value,
  })
}

const hasChildNotes = computed(() => {
  if (!shareInfo.value || !note.value) {
    return false;
  }
  return shareInfoStore.notes
    .some(n => n.parent === note.value!.id && n.id !== note.value!.id);
});

useAutofocus(note, 'text');
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
