<template>
    <v-stepper
      v-model="step"
      :items="['Upload', 'Select', 'Done']"
      :elevation="0"
      class="h-100 stepper-main"
    >
      <template #item.1>
        <div class="h-100 d-flex flex-column pa-4">
          <div class="flex-grow-1 overflow-y-auto d-flex flex-column">
            <v-file-upload 
              v-model="uploadForm.files"
              :multiple="true"
              density="compact"
              class="flex-grow-1"
            />
          </div>
          <s-select
            v-model="uploadForm.importer"
            :items="availableImporters"
            label="Importer"
            class="mt-4 flex-grow-0"
          />
        </div>
      </template>

      <template #item.2>
        <div v-if="selectForm.importAs === ImportAs.FINDINGS">
          <p v-if="parsedData.length === 0">No findings available for import.</p>
          <finding-list-selection
            :findings="parsedData as PentestFinding[]"
            v-model:selected-finding-ids="selectForm.selected"
          />
        </div>
        <div v-else-if="selectForm.importAs === ImportAs.NOTES">
          <p v-if="parsedData.length === 0">No notes available for import.</p>
          <note-tree-selection
            :note-group="groupNotes(parsedData as ProjectNote[])"
            v-model:selected-note-ids="selectForm.selected"
          />
        </div>
      </template>

      <template #item.3>
        <div class="h-100 d-flex flex-column justify-center align-center">
          <div class="text-center">
            <v-icon icon="mdi-check-circle" color="success" size="72" class="mb-4" />
            <h2 class="text-h4 mb-2">Import Complete!</h2>
            <p class="text-body-1 mb-6">
              {{ importedCount }} {{ selectForm.importAs === ImportAs.FINDINGS ? 'findings' : 'notes' }}
              have been successfully imported to your project.
            </p>
            
            <s-btn-primary
              v-if="selectForm.importAs === ImportAs.FINDINGS"
              :href="`/projects/${projectId}/reporting/`"
              target="_top"
              text="View Findings"
              prepend-icon="mdi-text"
              size="large"
            />
            <s-btn-primary
              v-else
              :href="`/projects/${projectId}/notes/`"
              target="_top"
              text="View Notes"
              prepend-icon="mdi-notebook"
              size="large"
            />
          </div>
        </div>
      </template>

      <template #next>
        <div v-if="step === Step.UPLOAD" class="mt-2">
          <btn-confirm
            :action="() => importScanFile(ImportAs.NOTES)"
            :confirm="false"
            button-text="Import as Notes"
            button-color="primary"
            :disabled="uploadForm.files.length === 0"
            class="mr-2"
          />
          <btn-confirm
            :action="() => importScanFile(ImportAs.FINDINGS)"
            :confirm="false"
            button-text="Import as Findings"
            button-color="primary"
            :disabled="uploadForm.files.length === 0"
          />
        </div>
        <btn-confirm
          v-else-if="step === Step.SELECT"
          :action="importSelectedObjects"
          :confirm="false"
          button-text="Import Selected"
          button-color="primary"
          :disabled="selectForm.selected.length === 0"
          class="mt-2"
        />
      </template>
    </v-stepper>
</template>

<script setup lang="ts">
import { uploadFileHelper, type NoteGroup, type PentestFinding, type ProjectNote } from "#imports";
import type { ParsedPentestFinding } from "~~/utils/types";

const appConfig = useAppConfig();
const route = useRoute();
const projectId = computed(() => route.params.projectId);

enum ImportAs {
  NOTES = 'notes',
  FINDINGS = 'findings',
}
enum Step {
  UPLOAD = 1,
  SELECT = 2,
  DONE = 3,
}

const availableImporters = await useFetchE<string[]>(`/api/plugins/${appConfig.pluginId}/api/availableimporters/`, { method: 'GET' });

const step = ref(Step.UPLOAD);
const uploadForm = ref({
  importer: 'auto',
  importAs: ImportAs.NOTES,
  files: [],
});
const parsedData = ref<ProjectNote[]|ParsedPentestFinding[]>([]);
const selectForm = ref({
  importAs: ImportAs.NOTES,
  selected: [] as string[],
});
const importedCount = ref(0);

async function importScanFile(importAs: ImportAs) {
  if (uploadForm.value.files.length === 0) {
    return;
  }

  try {
    parsedData.value = await uploadFileHelper(`/api/plugins/${appConfig.pluginId}/api/projects/${projectId.value}/parse/`, uploadForm.value.files, {
      importer: uploadForm.value.importer,
      import_as: importAs,
    });
    selectForm.value = {
      importAs,
      selected: parsedData.value.map(i => i.id),
    };
    step.value = Step.SELECT;
  } catch (error) {
    requestErrorToast({ error });
  }
}


async function createFinding(finding: ParsedPentestFinding) {
  try {
    await $fetch(`/api/v1/pentestprojects/${route.params.projectId}/findings/`, {
      method: 'POST',
      body: finding,
    });
    importedCount.value += 1;
  } catch (error) {
    requestErrorToast({ error, message: 'Failed to upload ' + finding.data.title });
  }
}

async function createNote(note: ProjectNote) {
  try {
    const res = await $fetch<ProjectNote>(`/api/v1/pentestprojects/${route.params.projectId}/notes/`, {
      method: 'POST',
      body: note,
    });
    importedCount.value += 1;
    return res;
  } catch (error) {
    requestErrorToast({ error, message: 'Failed to upload ' + note.title });
  }
}

async function importSelectedObjects() {
  importedCount.value = 0;
  if (selectForm.value.importAs === ImportAs.FINDINGS) {
    const findings = parsedData.value.filter(f => selectForm.value.selected.includes(f.id)) as ParsedPentestFinding[];
    await Promise.all(findings.map(createFinding));
  } else {
    const notes = parsedData.value.filter(n => selectForm.value.selected.includes(n.id)) as ProjectNote[];
    const groups = groupNotes(notes);
    async function createNoteGroup(group: NoteGroup<ProjectNote>, parentId?: string) {
      for (const g of group) {
        g.note.parent = parentId || null;
        const newNote = await createNote(g.note);
        if (newNote) {
          await createNoteGroup(g.children, newNote.id);
        }
      }
    }
    await createNoteGroup(groups);
  }
  
  step.value = Step.DONE;
}
</script>

<style lang="scss" scoped>
.stepper-main {
  display: flex;
  flex-direction: column;

  &:deep() {
    .v-stepper-header {
      flex-grow: 0;
      flex-shrink: 0;
    }
    .v-stepper-window {
      flex-grow: 1;
      min-height: 0;
      margin: 0;

      .v-window__container {
        height: 100%;
      }
      .v-stepper-window-item {
        height: 100%;
        overflow-y: auto;
      }
    }
  }
}
</style>

