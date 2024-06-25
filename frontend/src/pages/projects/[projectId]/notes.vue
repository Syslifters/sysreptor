<template>
  <split-menu v-model="localSettings.notebookInputMenuSize" :content-props="{ class: 'pa-0 h-100' }">
    <template #menu>
      <notes-menu
        title="Notes"
        :create-note="createNote"
        :perform-import="performImport"
        :export-url="`/api/v1/pentestprojects/${project.id}/notes/export/`"
        :export-name="'notes-' + project.name"
        :readonly="notesCollab.readonly.value"
      >
        <notes-sortable-list
          :model-value="noteGroups"
          @update:model-value="updateNoteOrder"
          @update:checked="updateNoteChecked"
          :disabled="notesCollab.readonly.value"
          :to-prefix="`/projects/${$route.params.projectId}/notes/`"
          :collab="notesCollab.collabProps.value"
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
import { debounce } from "lodash-es";

const route = useRoute();
const router = useRouter();
const localSettings = useLocalSettings();
const projectStore = useProjectStore();

definePageMeta({
  title: 'Notes',
});

const project = await useAsyncDataE(async () => await projectStore.getById(route.params.projectId as string), { key: 'projectnotes:project' });
const noteGroups = computed(() => projectStore.noteGroups(project.value.id));

const notesCollab = projectStore.useNotesCollab({ project: project.value });
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
    await projectStore.sortNotes(project.value, notes as NoteGroup<ProjectNote>);
  } catch (error) {
    requestErrorToast({ error });
  }
}, 0);
</script>
