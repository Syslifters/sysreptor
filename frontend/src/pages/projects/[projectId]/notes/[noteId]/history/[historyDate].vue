<template>
  <fetch-loader v-bind="fetchLoaderAttrs" class="h-100">
    <full-height-page v-if="project && note" :key="project.id + note.id">
      <template #header>
        <edit-toolbar v-bind="toolbarAttrs">
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
              v-if="currentUrl"
              :to="currentUrl" exact
              color="secondary" class="ml-1 mr-1 d-none d-lg-inline-flex"
              prepend-icon="mdi-undo"
              text="Back to current version"
            />
            <s-btn
              @click="historyVisible = !historyVisible"
              color="secondary"
              prepend-icon="mdi-history"
            >
              <span class="d-none d-lg-inline">Version History</span>
            </s-btn>
          </template>
        </edit-toolbar>
      </template>
      <template #default>
        <project-history-timeline
          v-model="historyVisible"
          :project="project"
          :note="note"
          :current-url="currentUrl"
        />

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
const route = useRoute();
const projectStore = useProjectStore();

const baseUrl = `/api/v1/pentestprojects/${route.params.projectId}/history/${route.params.historyDate}/notes/${route.params.noteId}/`;
const { data: note, project, readonly, toolbarAttrs, fetchLoaderAttrs, inputFieldAttrs } = useProjectLockEdit<ProjectNote>({
  baseUrl,
  fetchProjectType: false,
  historyDate: route.params.historyDate as string,
});
const historyVisible = ref(false);
const hasChildNotes = computed(() => false);
const currentUrl = computed(() => {
  if (projectStore.notes(project.value?.id || '').map(n => n.id).includes(note.value?.id || '')) {
    return `/projects/${project.value!.id}/notes/${note.value!.id}/`;
  }
  return null;
});

</script>

<style lang="scss" scoped>
.note-title {
  width: 100%;
}

.assignee-container {
  width: 17em;
  min-width: 17em;
}
</style>
