<template>
  <fetch-loader v-bind="fetchLoaderAttrs" class="h-100">
    <full-height-page v-if="note && fetchState.data.value">
      <template #header>
        <edit-toolbar v-bind="toolbarAttrs">
          <template #title>
            <div class="note-title-container">
              <div>
                <s-btn-icon
                  @click="note.checked = note.checked === null ? false : !note.checked ? true : null"
                  :icon="note.checked === null ? 'mdi-checkbox-blank-off-outline' : note.checked ? 'mdi-checkbox-marked' : 'mdi-checkbox-blank-outline'"
                  :disabled="true"
                  density="comfortable"
                />
              </div>
              <s-emoji-picker-field
                v-if="note.checked === null"
                v-model="note.icon_emoji"
                :empty-icon="hasChildNotes ? 'mdi-folder-outline' : 'mdi-note-text-outline'"
                :disabled="true"
                density="comfortable"
              />
              
              <markdown-text-field-content
                v-model="note.title"
                :disabled="true"
                :spellcheck-supported="true"
                v-bind="fieldAttrsHistoric"
                class="note-title"
              />
            </div>
          </template>
          <template #default>
            <div class="assignee-container ml-1 mr-1 d-none d-lg-block">
              <s-user-selection
                v-model="note.assignee"
                :selectable-users="fieldAttrsHistoric.selectableUsers"
                :disabled="true"
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
        <history-timeline-project
          v-model="historyVisible"
          :project="fetchState.data.value.projectHistoric"
          :note="note"
          :current-url="currentUrl"
        />
        
        <markdown-diff-page v-bind="markdownPageAttrs" />
      </template>
    </full-height-page>
  </fetch-loader>
</template>

<script setup lang="ts">
const route = useRoute();
const projectStore = useProjectStore();

const { obj: note, fetchState, fetchLoaderAttrs, toolbarAttrs, fieldAttrsHistoric, fieldAttrsCurrent } = useProjectHistory<ProjectNote>({
  subresourceUrlPart: `/notes/${route.params.noteId}/`,
});
const markdownPageAttrs = computed(() => ({
  historic: {
    value: fetchState.data.value?.dataHistoric?.text,
    ...fieldAttrsHistoric.value
  },
  current: {
    value: fetchState.data.value?.dataCurrent?.text,
    ...fieldAttrsCurrent.value
  },
}))

const historyVisible = ref(false);
const hasChildNotes = computed(() => false);
const currentUrl = computed(() => {
  if (projectStore.notes(fetchState.data.value?.projectHistoric.id || '').map(n => n.id).includes(note.value?.id || '')) {
    return `/projects/${fetchState.data.value!.projectHistoric.id}/notes/${note.value!.id}/`;
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
