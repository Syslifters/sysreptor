<template>
  <fetch-loader v-bind="fetchLoaderAttrs" class="h-100">
    <full-height-page v-if="note" :key="note.id">
      <template #header>
        <edit-toolbar v-bind="toolbarAttrs" :can-auto-save="true">
          <template #title>
            <div class="d-flex flex-row align-center">
              <div>
                <s-checkbox
                  :model-value="note.checked === null ? true : note.checked"
                  :indeterminate="note.checked === null"
                  @update:model-value="note.checked = note.checked === null ? false : !note.checked ? true : null"
                  :disabled="readonly"
                  true-icon="mdi-checkbox-marked"
                  false-icon="mdi-checkbox-blank-outline"
                  indeterminate-icon="mdi-checkbox-blank-off-outline"
                  color="inherit"
                  hide-details
                />
              </div>
              <s-emoji-picker-field
                v-if="note.checked === null"
                v-model="note.icon_emoji"
                :empty-icon="hasChildNotes ? 'mdi-folder-outline' : 'mdi-note-text-outline'"
                :disabled="readonly"
              />

              <markdown-text-field-content
                ref="titleRef"
                v-model="note.title"
                :disabled="readonly"
                :spellcheck-supported="true"
                v-bind="inputFieldAttrs"
                class="flex-grow-1"
              />

              <s-emoji-picker-field
                v-model="note.status_emoji"
                :disabled="readonly"
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
