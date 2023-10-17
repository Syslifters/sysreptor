<template>
  <split-menu v-model="localSettings.notebookInputMenuSize" :content-props="{ class: 'pa-0 h-100' }">
    <template #menu>
      <v-list density="compact" class="pb-0 h-100 d-flex flex-column">
        <div>
          <v-list-item-title class="text-h6 pl-2">{{ project.name }}</v-list-item-title>
        </div>

        <notes-sortable-list
          :model-value="noteGroups"
          @update:model-value="updateNoteOrder"
          @update:note="updateNote"
          :disabled="project.readonly"
          :to-prefix="`/projects/${$route.params.projectId}/notes/`"
          class="flex-grow-1 overflow-y-auto"
        />

        <div>
          <v-divider />
          <v-list-item>
            <btn-confirm
              :action="createNote"
              :disabled="project.readonly"
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
import { ProjectNote } from "~/utils/types";
import { NoteGroup } from "~/store/usernotes";

const route = useRoute();
const localSettings = useLocalSettings();
const projectStore = useProjectStore();

definePageMeta({
  title: 'Notes',
});

const project = await useAsyncDataE(async () => {
  const [project] = await Promise.all([
    projectStore.getById(route.params.projectId as string),
    projectStore.fetchNotes(route.params.projectId as string),
  ]);
  return project;
}, { key: 'projectnotes:notes' });
const noteGroups = computed(() => projectStore.noteGroups(project.value.id));

async function refreshListings() {
  try {
    await projectStore.fetchNotes(project.value.id);
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
  const currentNote = projectStore.notes(project.value.id).find(n => n.id === route.params.noteId);
  const obj = await projectStore.createNote(project.value, {
    title: 'New Note',
    // Insert new note after the currently selected note, or at the end of the list
    parent: currentNote?.parent || null,
    order: (currentNote ? currentNote.order + 1 : null),
    checked: [true, false].includes(currentNote?.checked as any) ? false : null,
  } as ProjectNote)
  // Reload note list to get updated order
  await refreshListings();

  await navigateTo({ path: `/projects/${project.value.id}/notes/${obj.id}/`, query: { focus: 'title' } })
}
async function updateNote(note: ProjectNote) {
  try {
    await projectStore.partialUpdateNote(project.value, note, ['checked']);
  } catch (error) {
    requestErrorToast({ error });
  }
}
// Execute in next tick: prevent two requests for events in the same tick
const updateNoteOrder = debounce(async (notes: NoteGroup<ProjectNote>) => {
  try {
    await projectStore.sortNotes(project.value, notes);
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
