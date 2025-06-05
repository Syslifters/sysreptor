<template>
  <split-menu v-model="localSettings.notebookInputMenuSize" :content-props="{ class: 'pa-0 h-100' }">
    <template #menu>
      <notes-menu
        title="Notes"
        v-model:search="notesCollab.search.value"
        :create-note="createNote"
        :perform-import="performImport"
        :perform-delete="performDelete"
        :perform-copy="performCopy"
        :export-url="`/api/v1/pentestprojects/${project.id}/notes/export/`"
        :export-name="'notes-' + project.name"
        :selected-notes="noteTreeRef?.selectedNotes"
        :readonly="notesCollab.readonly.value"
      >
        <notes-sortable-tree
          ref="noteTreeRef"
          :model-value="noteGroups"
          @update:model-value="updateNoteOrder"
          @update:checked="updateNoteChecked"
          :disabled="notesCollab.readonly.value"
          :to-prefix="`/projects/${route.params.projectId}/notes/`"
          :collab="notesCollab.collabProps.value"
        />
        <template #search>
          <notes-search-result-tree
            :model-value="noteSearchResults"
            :to-prefix="`/projects/${route.params.projectId}/notes/`"
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
const localSettings = useLocalSettings();
const projectStore = useProjectStore();

definePageMeta({
  title: 'Notes',
});

const project = await useAsyncDataE(async () => await projectStore.getById(route.params.projectId as string));
const notesCollab = projectStore.useNotesCollab({ project: project.value });
const noteGroups = computed(() => projectStore.noteGroups(project.value.id));
const noteSearchResults = computed(() => searchNotes(projectStore.notes(project.value.id), notesCollab.collabProps.value.search));

const noteTreeRef = useTemplateRef('noteTreeRef');

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
  const currentNote = projectStore.notes(project.value.id).find(n => n.id === route.params.noteId);
  const obj = await projectStore.createNote(project.value, {
    title: 'New Note',
    // Insert new note after the currently selected note, or at the end of the list
    parent: currentNote?.parent || null,
    order: (currentNote ? currentNote.order + 1 : undefined),
    checked: [true, false].includes(currentNote?.checked as any) ? false : null,
  })
  await navigateTo({ path: `/projects/${project.value.id}/notes/${obj.id}/`, hash: '#title' })
}
async function performImport(file: File) {
  const res = await uploadFileHelper<ProjectNote[]>(`/api/v1/pentestprojects/${project.value.id}/notes/import/`, file);
  const note = res.find(n => n.parent === null)!;
  await navigateTo(`/projects/${project.value.id}/notes/${note.id}/`);
}
async function performDelete(note: NoteBase) {
  await projectStore.deleteNote(project.value, note as ProjectNote);
}
async function performCopy(note: NoteBase) {
  await projectStore.copyNote(project.value, note as ProjectNote);
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
    await projectStore.sortNotes(project.value, notes as NoteGroup<ProjectNote>);
  } catch (error) {
    requestErrorToast({ error });
  }
}

useHeadExtended({
  syncState: notesCollab.syncState,
});
</script>
