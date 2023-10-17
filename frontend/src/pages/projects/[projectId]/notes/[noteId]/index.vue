<template>
  <fetch-loader v-bind="fetchLoaderAttrs" class="h-100">
    <full-height-page v-if="project && note" :key="project.id + note.id">
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
          <template #default>
            <div class="assignee-container ml-1 mr-1 d-none d-lg-block">
              <s-user-selection
                v-model="note.assignee"
                :selectable-users="project.members"
                :disabled="readonly"
                label="Assignee"
                variant="underlined"
                density="compact"
              />
            </div>

            <s-btn
              @click="historyVisible = !historyVisible"
              color="secondary"
              prepend-icon="mdi-history"
            >
              <span class="d-none d-lg-inline">Version History</span>
            </s-btn>
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
        <project-history-timeline
          v-model="historyVisible"
          :project="project"
          :note="note"
          :current-url="route.fullPath"
        />

        <markdown-page
          ref="textRef"
          v-model="note.text"
          :disabled="readonly"
          :lang="project.language"
          v-bind="inputFieldAttrs"
        />
      </template>
    </full-height-page>
  </fetch-loader>
</template>

<script setup lang="ts">
import urlJoin from "url-join";

const route = useRoute();
const projectStore = useProjectStore();

const baseUrl = `/api/v1/pentestprojects/${route.params.projectId}/notes/${route.params.noteId}/`;
const { data: note, project, readonly, toolbarAttrs, fetchLoaderAttrs, inputFieldAttrs } = useProjectLockEdit({
  baseUrl,
  fetchProjectType: false,
  canUploadFiles: true,
  performSave: projectStore.partialUpdateNote,
  performDelete: async (project, note) => {
    await projectStore.deleteNote(project, note);
    await navigateTo(`/projects/${project.id}/notes/`);
  },
  updateInStore: projectStore.setNote,
  autoSaveOnUpdateData({ oldValue, newValue }): boolean {
    return oldValue.checked !== newValue.checked ||
        oldValue.status_emoji !== newValue.status_emoji ||
        oldValue.icon_emoji !== newValue.icon_emoji ||
        oldValue.assignee !== newValue.assignee;
  }
});
const historyVisible = ref(false);
const exportPdfUrl = computed(() => urlJoin(baseUrl, '/export-pdf/'));
const hasChildNotes = computed(() => {
  if (!project.value || !note.value) {
    return false;
  }
  return projectStore.notes(project.value.id)
    .some(n => n.parent === note.value!.id && n.id !== note.value!.id);
});

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
.assignee-container {
  width: 17em;
  min-width: 17em;
}
</style>
