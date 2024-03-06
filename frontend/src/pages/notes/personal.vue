<template>
  <split-menu v-model="localSettings.notebookInputMenuSize" :content-props="{ class: 'pa-0 h-100' }">
    <template #menu>
      <notes-menu
        title="Personal Notes"
        :create-note="createNote"
        :perform-import="performImport"
        :export-url="`/api/v1/pentestusers/self/notes/export/`"
        :export-name="'notes-' + auth.user.value!.username"
      >
        <notes-sortable-list
          :model-value="noteGroups"
          @update:model-value="updateNoteOrder"
          @update:checked="updateNote"
          to-prefix="/notes/personal/"
        />
      </notes-menu>
    </template>

    <template #default>
      <nuxt-page />
    </template>
  </split-menu>
</template>

<script setup lang="ts">
import debounce from "lodash/debounce";

const route = useRoute();
const auth = useAuth();
const localSettings = useLocalSettings();
const userNotesStore = useUserNotesStore();

useHeadExtended({
  titleTemplate: (title?: string|null) => userNotesTitleTemplate(title, route),
  breadcrumbs: () => [{ title: 'Personal Notes', to: '/notes/personal/' }],
});

await useAsyncDataE(async () => await userNotesStore.fetchNotes());
const noteGroups = computed(() => userNotesStore.noteGroups);

async function refreshListings() {
  try {
    await userNotesStore.fetchNotes();
  } catch (error) {
    // hide error
  }
}
const refreshListingsInterval = ref();
onMounted(() => {
  refreshListingsInterval.value = setInterval(refreshListings, 10_000);
});
onBeforeUnmount(() => {
  if (refreshListingsInterval.value) {
    clearInterval(refreshListingsInterval.value);
    refreshListingsInterval.value = undefined;
  }
});

async function createNote() {
  const currentNote = userNotesStore.notes.find(n => n.id === route.params.noteId);
  const obj = await userNotesStore.createNote({
    title: 'New Note',
    // Insert new note after the currently selected note, or at the end of the list
    parent: currentNote?.parent || null,
    order: (currentNote ? currentNote.order + 1 : null),
    checked: [true, false].includes(currentNote?.checked as any) ? false : null,
  } as UserNote);
  // Reload note list to get updated order
  await refreshListings();
  await navigateTo({ path: `/notes/personal/${obj.id}/`, query: { focus: 'title' } });
}
async function performImport(file: File) {
  const res = await uploadFileHelper<UserNote[]>(`/api/v1/pentestusers/self/notes/import/`, file);
  const note = res.find(n => n.parent === null)!;
  await refreshListings();
  await navigateTo(`/notes/personal/${note.id}/`);
}
async function updateNote(note: ProjectNote) {
  try {
    await userNotesStore.partialUpdateNote(note, ['checked']);
  } catch (error) {
    requestErrorToast({ error });
  }
}
// Execute in next tick: prevent two requests for events in the same tick
const updateNoteOrder = debounce(async (notes: NoteGroup<UserNote>) => {
  try {
    await userNotesStore.sortNotes(notes);
  } catch (error) {
    requestErrorToast({ error });
  }
}, 0);
</script>
