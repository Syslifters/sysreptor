<template>
  <v-form ref="form" class="h-100">
    <split-menu v-model="localSettings.defaultNotesDefinitionMenuSize" :content-props="{ class: 'pa-0 h-100' }">
      <template #menu>
        <notes-menu
          title="Initial Notes"
          :create-note="createNote"
          :readonly="readonly"
        >
          <notes-sortable-list
            v-model="noteGroups"
            :selected="currentNote"
            @update:selected="selectNote"
            @update:checked="updateNoteChecked"
            :disabled="readonly"
          />
        </notes-menu>
      </template>
      <template #default>
        <full-height-page>
          <template #header>
            <edit-toolbar v-bind="toolbarAttrs" :form="$refs.form as VForm">
              <template #title v-if="currentNote">
                <div class="note-title-container">
                  <div>
                    <s-btn-icon
                      @click="currentNote.checked = currentNote.checked === null ? false : !currentNote.checked ? true : null"
                      :icon="currentNote.checked === null ? 'mdi-checkbox-blank-off-outline' : currentNote.checked ? 'mdi-checkbox-marked' : 'mdi-checkbox-blank-outline'"
                      :disabled="readonly"
                      density="comfortable"
                    />
                  </div>
                  <s-emoji-picker-field
                    v-if="currentNote.checked === null"
                    v-model="currentNote.icon_emoji"
                    :empty-icon="hasChildNotes ? 'mdi-folder-outline' : 'mdi-note-text-outline'"
                    :readonly="readonly"
                    density="comfortable"
                  />
              
                  <markdown-text-field-content
                    ref="titleRef"
                    v-model="currentNote.title"
                    :readonly="readonly"
                    :spellcheck-supported="true"
                    :lang="projectType.language"
                    v-model:spellcheck-enabled="localSettings.designSpellcheckEnabled"
                    class="note-title"
                  />
                </div>
              </template>
              <template #context-menu v-if="currentNote">
                <btn-delete
                  :delete="() => deleteNote(currentNote!)"
                  :disabled="readonly"
                  button-variant="list-item"
                  color="error"
                />
              </template>
            </edit-toolbar>
          </template>
          <template #default>
            <markdown-page
              v-if="currentNote"
              ref="textRef"
              v-model="currentNote.text"
              :readonly="readonly"
              :lang="projectType.language"
              v-model:spellcheck-enabled="localSettings.designSpellcheckEnabled"
              v-model:markdown-editor-mode="localSettings.designMarkdownEditorMode"
            />
            <v-empty-state v-else>
              <template #media>
                <img src="@base/assets/dino/project.svg" alt="" class="img-raptor" />
              </template>
              <template #text>
                <strong>Define initial notes applied to new projects</strong>
              </template>
            </v-empty-state>
          </template>
        </full-height-page>
      </template>
    </split-menu>
  </v-form>
</template>

<script setup lang="ts">
import { VForm } from 'vuetify/components';
import { uuidv4 } from "@base/utils/helpers";

const localSettings = useLocalSettings();

const { projectType, toolbarAttrs, readonly } = useProjectTypeLockEdit(await useProjectTypeLockEditOptions({
  save: true,
  saveFields: ['default_notes'],
}));

const currentNote = ref<NoteBase|null>(null);
const hasChildNotes = computed(() => projectType.value.default_notes.some(n => n.parent === currentNote.value?.id));
const noteGroups = computed({
  get: () => groupNotes(projectType.value.default_notes),
  set: (val) => {
    const notes = [] as NoteBase[];
    sortNotes(val, (n) => { 
      notes.push(n); 
    });
    projectType.value.default_notes = notes;
    currentNote.value = projectType.value.default_notes.find(n => n.id === currentNote.value?.id) || null;
  },
})

const titleRef = ref();
const textRef = ref();
async function createNote() {
  const newNote = {
    id: uuidv4(),
    parent: null,
    order: noteGroups.value.length + 1,
    checked: null,
    icon_emoji: null,
    title: 'New Note',
    text: '',
  } as NoteBase;

  if (currentNote.value) {
    // Insert after current note
    newNote.parent = currentNote.value.parent;
    newNote.order = currentNote.value.order + 1;
    newNote.checked = [true, false].includes(currentNote.value.checked as any) ? false : null;
    // Make space after current note
    for (const n of projectType.value.default_notes) {
      if (n.parent === newNote.parent && n.order >= newNote.order) {
        n.order += 1;
      }
    }
  }
  projectType.value.default_notes.push(newNote);
  currentNote.value = newNote;
  await nextTick();
  titleRef.value?.focus();
}
function deleteNote(note: NoteBase) {
  // Recursively delete child notes
  projectType.value.default_notes
    .filter(n => n.parent === note.id)
    .forEach(n => deleteNote(n));

  // Delete note
  projectType.value.default_notes = projectType.value.default_notes.filter(n => n.id !== note.id);
  if (currentNote.value?.id === note.id) {
    currentNote.value = null;
  }
}
function updateNoteChecked(note: NoteBase) {
  const dn = projectType.value.default_notes.find(n => n.id === note.id);
  if (dn) {
    dn.checked = note.checked;
  }
}
async function selectNote(note: NoteBase|null) {
  currentNote.value = note;
  await nextTick();
  textRef.value?.focus();
}

</script>

<style scoped lang="scss">
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

.img-raptor {
  width: 30em;
  max-width: 50%;
  max-height: 50vh;
  pointer-events: none;
  user-select: none;
}
</style>
