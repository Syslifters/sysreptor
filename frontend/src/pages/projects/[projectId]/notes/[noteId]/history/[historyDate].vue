<template>
  <fetch-loader v-bind="fetchLoaderAttrs" class="h-100">
    <full-height-page v-if="project && note" :key="project.id + note.id">
      <template #header>
        <edit-toolbar v-bind="toolbarAttrs">
          <template #title>
            <div class="note-title-container">
              <div>
                <s-btn-icon
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

            <s-btn-secondary
              v-if="currentUrl"
              :to="currentUrl" exact
              class="ml-1 mr-1 d-none d-lg-inline-flex"
              prepend-icon="mdi-undo"
              text="Back to current version"
            />
            <btn-history v-model="historyVisible" />
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
const localSettings = useLocalSettings();
const projectStore = useProjectStore();

const baseUrl = `/api/v1/pentestprojects/${route.params.projectId}/history/${route.params.historyDate}/notes/${route.params.noteId}/`;
const { data: note, project, readonly, toolbarAttrs, fetchLoaderAttrs, inputFieldAttrs } = useProjectLockEdit<ProjectNote>({
  baseUrl,
  fetchProjectType: false,
  historyDate: route.params.historyDate as string,
  markdownEditorMode: computed({ get: () => localSettings.projectNoteMarkdownEditorMode, set: (val) => { localSettings.projectNoteMarkdownEditorMode = val } }),
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

.assignee-container {
  width: 17em;
  min-width: 17em;
}
</style>
