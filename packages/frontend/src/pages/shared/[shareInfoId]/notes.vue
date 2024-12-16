<template>
  <split-menu v-model="localSettings.notebookInputMenuSize" :content-props="{ class: 'pa-0 h-100' }">
    <template #menu>
      <notes-menu
        title="Notes"
        v-model:search="notesCollab.search.value"
        :create-note="createNote"
        :readonly="notesCollab.readonly.value"
      >
        <notes-sortable-list
          :model-value="noteGroups"
          @update:checked="updateNoteChecked"
          :disabled="true"
          :to-prefix="`/shared/${route.params.shareInfoId}/notes/`"
          :collab="notesCollab.collabProps.value"
        />
        <template #search>
          <notes-search-result-list
            :result-group="noteSearchResults"
            :to-prefix="`/shared/${route.params.projectId}/notes/`"
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
const shareInfoStore = useShareInfoStore();

definePageMeta({
  auth: false,
  layout: 'public',
});

const shareInfo = await useAsyncDataE(async () => {
  try {
    const shareInfo = await shareInfoStore.getById(route.params.shareInfoId as string);
    if (shareInfo.password_required && !shareInfo.password_verified) {
      throw new Error('Password required');
    }

    // Set markdown editor mode based on permissions
    if (!shareInfo.permissions_write) {
      localSettings.sharedNoteMarkdownEditorMode = MarkdownEditorMode.PREVIEW;
    } else {
      localSettings.sharedNoteMarkdownEditorMode = localSettings.sharedNoteMarkdownEditorMode === MarkdownEditorMode.PREVIEW ? 
        MarkdownEditorMode.MARKDOWN_AND_PREVIEW : 
        localSettings.sharedNoteMarkdownEditorMode;
    }

    // Select root note if no other note is selected
    if (shareInfo && !route.params.noteId) {
      await navigateTo(`/shared/${shareInfo.id}/notes/${shareInfo.note_id}`);
    }

    return shareInfo;
  } catch {
    await navigateTo(`/shared/${route.params.shareInfoId}/`);
    return null;
  }
});

const notesCollab = shareInfoStore.useNotesCollab({ shareInfo: shareInfo.value! });
const noteGroups = computed(() => shareInfoStore.noteGroups);
const noteSearchResults = computed(() => searchNotes(shareInfoStore.notes, notesCollab.collabProps.value.search));

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
  let currentNote = shareInfoStore.notes.find(n => n.id === route.params.noteId) || null;
  let parentNoteId = currentNote?.parent;
  if (!parentNoteId || !shareInfoStore.notes.find(n => n.id === parentNoteId)) {
    parentNoteId = shareInfoStore.noteGroups[0]!.note.id;
    currentNote = shareInfoStore.noteGroups[0]!.children.at(-1)?.note || null;
  }
  const obj = await shareInfoStore.createNote(shareInfo.value!, {
    title: 'New Note',
    // Insert new note after the currently selected note, or at the end of the list
    parent: parentNoteId,
    order: (currentNote ? currentNote.order + 1 : undefined),
    checked: [true, false].includes(currentNote?.checked as any) ? false : null,
  })
  await navigateTo({ path: `/shared/${shareInfo.value!.id}/notes/${obj.id}/`, hash: '#title' })
}

function updateNoteChecked(note: NoteBase) {
  notesCollab.onCollabEvent({
    type: CollabEventType.UPDATE_KEY,
    path: collabSubpath(notesCollab.collabProps.value, `notes.${note.id}.checked`).path,
    value: note.checked,
  });
}
</script>
