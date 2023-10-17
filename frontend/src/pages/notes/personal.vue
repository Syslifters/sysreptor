<template>
  <split-menu v-model="localSettings.notebookInputMenuSize" :content-props="{ class: 'pa-0 h-100' }">
    <template #menu>
      <v-list density="compact" class="pb-0 h-100 d-flex flex-column">
        <div>
          <v-list-item-title class="text-h6 pl-2">Personal Notes</v-list-item-title>
        </div>

        <notes-sortable-list
          :model-value="noteGroups"
          @update:model-value="updateNoteOrder"
          @update:note="updateNote"
          to-prefix="/notes/personal/"
          class="flex-grow-1 overflow-y-auto"
        />

        <div>
          <v-divider />
          <v-list-item>
            <btn-confirm
              :action="createNote"
              :confirm="false"
              button-text="Add"
              button-icon="mdi-plus"
              tooltip-text="Add Note (Ctrl+J)"
              keyboard-shortcut="ctrl+j"
              size="small"
              block
            />
          </v-list-item>
        </div>
      </v-list>
    </template>

    <template #default>
      <nuxt-page />
    </template>
  </split-menu>
</template>

<script setup lang="ts">
import debounce from "lodash/debounce";

const route = useRoute();
const localSettings = useLocalSettings();
const userNotesStore = useUserNotesStore();

useHead({
  titleTemplate: (title?: string|null) => userNotesTitleTemplate(title, route),
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

<style lang="scss" scoped>
.note-checked {
  display: inline-block;
  margin: 0;
  padding: 0;
}
</style>
