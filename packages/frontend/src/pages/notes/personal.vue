<template>
  <split-menu v-model="localSettings.notebookInputMenuSize" :content-props="{ class: 'pa-0 h-100' }">
    <template #menu>
      <notes-menu
        title="Personal Notes"
        v-model:search="notesCollab.search.value"
        :create-note="createNote"
        :perform-import="performImport"
        :perform-delete="performDelete"
        :perform-copy="performCopy"
        :export-url="`/api/v1/pentestusers/self/notes/export/`"
        :export-name="'notes-' + auth.user.value!.username"
        :selected-notes="noteTreeRef?.selectedNotes"
        :readonly="notesCollab.readonly.value"
      >
        <notes-sortable-tree
          ref="noteTreeRef"
          :model-value="noteGroups"
          @update:model-value="updateNoteOrder"
          @update:checked="updateNoteChecked"
          :disabled="notesCollab.readonly.value"
          to-prefix="/notes/personal/"
        />
        <template #search>
          <notes-search-result-tree
            :model-value="noteSearchResults"
            to-prefix="/notes/personal/"
          />
        </template>
      </notes-menu>
    </template>

    <template #default>
      <collab-loader :collab="notesCollab">
        <nuxt-page />
      </collab-loader>
    </template>
  </split-menu>
</template>

<script setup lang="ts">
const route = useRoute();
const router = useRouter();
const auth = useAuth();
const localSettings = useLocalSettings();
const userNotesStore = useUserNotesStore();

const notesCollab = userNotesStore.useNotesCollab();
const noteGroups = computed(() => userNotesStore.noteGroups);
const noteSearchResults = computed(() => searchNotes(userNotesStore.notes, notesCollab.collabProps.value.search));

const noteTreeRef = useTemplateRef('noteTreeRef');

useHeadExtended({
  titleTemplate: (title?: string|null) => userNotesTitleTemplate(title, route),
  breadcrumbs: () => [{ title: 'Personal Notes', to: '/notes/personal/' }],
  syncState: notesCollab.syncState,
});

onMounted(async () => {
  await notesCollab.connect();
  collabAwarenessSendNavigate();
});
onBeforeUnmount(async () => {
  await notesCollab.disconnect();
});
watch(() => router.currentRoute.value, collabAwarenessSendNavigate);
function collabAwarenessSendNavigate() {
  const noteId = router.currentRoute.value.params.noteId;
  notesCollab.onCollabEvent({
    type: CollabEventType.AWARENESS,
    path: collabSubpath(notesCollab.collabProps.value, noteId ? `notes.${noteId}` : null).path,
  });
}

async function createNote() {
  const currentNote = userNotesStore.notes.find(n => n.id === route.params.noteId);
  const obj = await userNotesStore.createNote({
    title: 'New Note',
    // Insert new note after the currently selected note, or at the end of the list
    parent: currentNote?.parent || null,
    order: (currentNote ? currentNote.order + 1 : undefined),
    checked: [true, false].includes(currentNote?.checked as any) ? false : null,
  });
  await navigateTo({ path: `/notes/personal/${obj.id}/`, hash: 'title' });
}
async function performDelete(note: NoteBase) {
  return await userNotesStore.deleteNote(note as UserNote);
}
async function performImport(file: File) {
  const res = await uploadFileHelper<UserNote[]>(`/api/v1/pentestusers/self/notes/import/`, file);
  const note = res.find(n => n.parent === null)!;
  await navigateTo(`/notes/personal/${note.id}/`);
}
async function performCopy(note: NoteBase) {
  await userNotesStore.copyNote(note as UserNote);
}
function updateNoteChecked(note: NoteBase) {
  notesCollab.onCollabEvent({
    type: CollabEventType.UPDATE_KEY,
    path: collabSubpath(notesCollab.collabProps.value, `notes.${note.id}.checked`).path,
    value: note.checked,
  });
}

async function updateNoteOrder(notes: NoteGroup<NoteBase>) {
  try {
    await userNotesStore.sortNotes(notes as NoteGroup<UserNote>);
  } catch (error) {
    requestErrorToast({ error });
  }
}

useHeadExtended({
  syncState: notesCollab.syncState,
});
</script>
