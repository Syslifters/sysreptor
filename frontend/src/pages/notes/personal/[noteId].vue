<template>
  <fetch-loader v-bind="fetchLoaderAttrs" class="h-100">
    <full-height-page v-if="note" :key="note.id">
      <template #header>
        <edit-toolbar v-bind="toolbarAttrs" :can-auto-save="true">
          <template #title>
            <div class="note-title-container">
              <div>
                <s-btn
                  @click="note.checked = note.checked === null ? false : !note.checked ? true : null"
                  :icon="note.checked === null ? 'mdi-checkbox-blank-off-outline' : note.checked ? 'mdi-checkbox-marked' : 'mdi-checkbox-blank-outline'"
                  :disabled="readonly"
                  density="comfortable"
                />
              </div>
              <s-emoji-picker-field
                v-if="note.checked === null"
                v-model="note.icon_emoji"
                :empty-icon="hasChildNotes ? 'mdi-folder-outline' : 'mdi-note-text-outline'"
                :disabled="readonly"
                density="comfortable"
              />
              
              <markdown-text-field-content
                ref="titleRef"
                v-model="note.title"
                :disabled="readonly"
                :spellcheck-supported="true"
                v-bind="inputFieldAttrs"
                class="note-title"
              />
              
              <s-emoji-picker-field
                v-model="note.status_emoji"
                :disabled="readonly"
                density="comfortable"
              />
            </div>
          </template>
          <template #context-menu>
            <btn-export
              :export-url="exportPdfUrl"
              :name="note.title"
              extension=".pdf"
              button-text="Export as PDF"
            />
          </template>
        </edit-toolbar>
      </template>
      <template #default>
        <markdown-page
          ref="textRef"
          v-model="note.text"
          :disabled="readonly"
          v-bind="inputFieldAttrs"
        />
      </template>
    </full-height-page>
  </fetch-loader>
</template>

<script setup lang="ts">
import urlJoin from "url-join";
import { uploadFileHelper } from "~/utils/upload";
import { UploadedFileInfo } from "~/utils/types";

const route = useRoute();
const userNotesStore = useUserNotesStore();

const baseUrl = computed(() => `/api/v1/pentestusers/self/notes/${route.params.noteId}/`);
const fetchState = useLazyFetch<UserNote>(baseUrl.value, { method: 'GET' });
const note = computed(() => fetchState.data.value);
const { readonly, toolbarAttrs, fetchLoaderAttrs } = useLockEdit({
  baseUrl,
  data: fetchState.data,
  fetchState,
  performSave: async n => await userNotesStore.partialUpdateNote(n!),
  performDelete: async (n) => {
    await userNotesStore.deleteNote(n!);
    await navigateTo('/notes/personal/');
  },
  updateInStore: n => userNotesStore.setNote(n!),
  autoSaveOnUpdateData({ oldValue, newValue }): boolean {
    return oldValue!.checked !== newValue!.checked ||
        oldValue!.status_emoji !== newValue!.status_emoji ||
        oldValue!.icon_emoji !== newValue!.icon_emoji;
  }
});
const exportPdfUrl = computed(() => urlJoin(baseUrl.value, '/export-pdf/'));
const hasChildNotes = computed(() => {
  if (!note.value) {
    return false;
  }
  return userNotesStore.notes
    .some(n => n.parent === note.value!.id && n.id !== note.value!.id);
});

async function uploadFile(file: File) {
  const obj = await uploadFileHelper<UploadedFileInfo>('/api/v1/pentestusers/self/notes/upload/', file);
  if (obj.resource_type === 'file') {
    return `[${obj.name}](/files/name/${obj.name})`;
  } else {
    return `![](/images/name/${obj.name})`;
  }
}
function rewriteFileUrl(imgSrc: string) {
  return urlJoin('/api/v1/pentestusers/self/notes/', imgSrc);
}
const inputFieldAttrs = computed(() => ({
  lang: 'auto',
  uploadFile,
  rewriteFileUrl,
}));

// Autofocus input
const titleRef = ref();
const textRef = ref();
watch(() => fetchLoaderAttrs.value.fetchState.pending, async (pending) => {
  if (!pending) {
    await nextTick();
    if (route.query?.focus === 'title') {
      titleRef.value?.focus();
    } else {
      textRef.value?.focus();
    }
  }
});
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
