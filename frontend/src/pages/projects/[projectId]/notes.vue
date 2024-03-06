<template>
  <split-menu v-model="localSettings.notebookInputMenuSize" :content-props="{ class: 'pa-0 h-100' }">
    <template #menu>
      <notes-menu
        title="Notes"
        :create-note="createNote"
        :perform-import="performImport"
        :export-url="`/api/v1/pentestprojects/${project.id}/notes/export/`"
        :export-name="'notes-' + project.name"
        :readonly="project.readonly"
      >
        <notes-sortable-list
          :model-value="noteGroups"
          @update:model-value="updateNoteOrder"
          @update:checked="updateNoteChecked"
          :disabled="project.readonly"
          :to-prefix="`/projects/${$route.params.projectId}/notes/`"
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
const localSettings = useLocalSettings();
const projectStore = useProjectStore();

definePageMeta({
  title: 'Notes',
});

const project = await useAsyncDataE(async () => await projectStore.getById(route.params.projectId as string), { key: 'projectnotes:project' });
const noteGroups = computed(() => projectStore.noteGroups(project.value.id));

const notesCollab = projectStore.useNotesCollab(project.value);
watch(notesCollab.connectionState, (val) => {
  console.log('notesCollab.connectionState', val);
});
watch(() => notesCollab.data.value, (val) => {
  console.log('notesCollab.data', val);
}, { deep: true });

onMounted(() => {
  notesCollab.connect();
});
onBeforeUnmount(() => {
  notesCollab.disconnect();
});

async function createNote() {
  const currentNote = projectStore.notes(project.value.id).find(n => n.id === route.params.noteId);
  const obj = await projectStore.createNote(project.value, {
    title: 'New Note',
    // Insert new note after the currently selected note, or at the end of the list
    parent: currentNote?.parent || null,
    order: (currentNote ? currentNote.order + 1 : null),
    checked: [true, false].includes(currentNote?.checked as any) ? false : null,
  } as unknown as ProjectNote)
  await navigateTo({ path: `/projects/${project.value.id}/notes/${obj.id}/`, query: { focus: 'title' } })
}
async function performImport(file: File) {
  const res = await uploadFileHelper<ProjectNote[]>(`/api/v1/pentestprojects/${project.value.id}/notes/import/`, file);
  const note = res.find(n => n.parent === null)!;
  await navigateTo(`/projects/${project.value.id}/notes/${note.id}/`);
}

function updateNoteChecked(note: ProjectNote) {
  useEventBus('collab.update_key').emit({ 
    path: collabSubpath(notesCollab.props.value, `notes.${note.id}.checked`).path, 
    value: note.checked,
  });
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
