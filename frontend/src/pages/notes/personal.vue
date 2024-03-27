<template>
  <split-menu v-model="localSettings.notebookInputMenuSize" :content-props="{ class: 'pa-0 h-100' }">
    <template #menu>
      <notes-menu
        title="Personal Notes"
        :create-note="createNote"
        :perform-import="performImport"
        :export-url="`/api/v1/pentestusers/self/notes/export/`"
        :export-name="'notes-' + auth.user.value!.username"
        :readonly="notesCollab.readonly.value"
      >
        <notes-sortable-list
          :model-value="noteGroups"
          @update:model-value="updateNoteOrder"
          @update:checked="updateNoteChecked"
          :disabled="notesCollab.readonly.value"
          to-prefix="/notes/personal/"
        />
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
import debounce from "lodash/debounce";

const route = useRoute();
const router = useRouter();
const auth = useAuth();
const localSettings = useLocalSettings();
const userNotesStore = useUserNotesStore();

useHeadExtended({
  titleTemplate: (title?: string|null) => userNotesTitleTemplate(title, route),
  breadcrumbs: () => [{ title: 'Personal Notes', to: '/notes/personal/' }],
});

const noteGroups = computed(() => userNotesStore.noteGroups);

const notesCollab = userNotesStore.useNotesCollab();
onMounted(async () => {
  if (notesCollab.hasEditPermissions.value) {
    await notesCollab.connect();
    collabAwarenessSendNavigate();
  } else {
    await userNotesStore.fetchNotes();
  }
});
onBeforeUnmount(() => {
  notesCollab.disconnect();
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
    order: (currentNote ? currentNote.order + 1 : null),
    checked: [true, false].includes(currentNote?.checked as any) ? false : null,
  } as UserNote);
  await navigateTo({ path: `/notes/personal/${obj.id}/`, query: { focus: 'title' } });
}
async function performImport(file: File) {
  const res = await uploadFileHelper<UserNote[]>(`/api/v1/pentestusers/self/notes/import/`, file);
  const note = res.find(n => n.parent === null)!;
  await navigateTo(`/notes/personal/${note.id}/`);
}
function updateNoteChecked(note: NoteBase) {
  notesCollab.onCollabEvent({
    type: CollabEventType.UPDATE_KEY,
    path: collabSubpath(notesCollab.collabProps.value, `notes.${note.id}.checked`).path,
    value: note.checked,
  });
}
// Execute in next tick: prevent two requests for events in the same tick
const updateNoteOrder = debounce(async (notes: NoteGroup<NoteBase>) => {
  try {
    await userNotesStore.sortNotes(notes as NoteGroup<UserNote>);
  } catch (error) {
    requestErrorToast({ error });
  }
}, 0);
</script>
