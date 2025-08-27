<template>
  <v-container fluid class="h-100">
    <h1 class="mb-4">Scan Import Plugin</h1>
    <v-form>
      <v-row>
        <v-col cols="6">
          <s-file-input
            v-model="uploadForm.files"
            label="File"
            :multiple="true"
          />
        </v-col>
        <v-col cols="6">
          <s-select
            v-model="uploadForm.importer"
            :items="availableImporters"
            label="Importer"
          />
        </v-col>
        <v-col cols="12">
          <div>
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
        </v-col>
      </v-row>
    </v-form>

    <div v-if="step === Step.SELECT" class="mt-4">
      <div v-if="selectForm.importAs === ImportAs.FINDINGS">
        <finding-list-selection
          :findings="parsedData as PentestFinding[]"
          v-model:selected-finding-ids="selectForm.selected"
        />
      </div>
      <div v-else-if="selectForm.importAs === ImportAs.NOTES">
        <note-tree-selection
          :note-group="groupNotes(parsedData as ProjectNote[])"
          v-model:selected-note-ids="selectForm.selected"
        />
      </div>
      <btn-confirm
        :action="importSelectedObjects"
        :confirm="false"
        button-text="Import Selected"
        button-color="primary"
        :disabled="selectForm.selected.length === 0"
      />
    </div>
  </v-container>
</template>

<script setup lang="ts">
import { uploadFileHelper, type NoteGroup, type PentestFinding, type ProjectNote } from "#imports";

const appConfig = useAppConfig()
const route = useRoute();

enum ImportAs {
  NOTES = 'notes',
  FINDINGS = 'findings',
}
enum Step {
  UPLOAD,
  SELECT,
  DONE,
}

const availableImporters = await useFetchE<string[]>(`/api/plugins/${appConfig.pluginId}/api/projects/${route.params.projectId}/availableimporters/`, { method: 'GET' });

const step = ref(Step.UPLOAD);
const uploadForm = ref({
  importer: 'auto',
  importAs: ImportAs.NOTES,
  files: [],
});
const parsedData = ref<ProjectNote[]|PentestFinding[]>([]);
const selectForm = ref({
  importAs: ImportAs.NOTES,
  selected: [] as string[],
})

async function importScanFile(importAs: ImportAs) {
  if (uploadForm.value.files.length === 0) {
    return;
  }

  try {
    parsedData.value = await uploadFileHelper(`/api/plugins/${appConfig.pluginId}/api/projects/${route.params.projectId}/parse/`, uploadForm.value.files, {
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


async function createFinding(finding: PentestFinding) {
  try {
    await $fetch(`/api/v1/pentestprojects/${route.params.projectId}/findings/`, {
      method: 'POST',
      body: finding,
    });
  } catch (error) {
    requestErrorToast({ error, message: 'Failed to upload ' + finding.data.title });
  }
}

async function createNote(note: ProjectNote) {
  try {
    return await $fetch<ProjectNote>(`/api/v1/pentestprojects/${route.params.projectId}/notes/`, {
      method: 'POST',
      body: note,
    });
  } catch (error) {
    requestErrorToast({ error, message: 'Failed to upload ' + note.title });
  }
}

async function importSelectedObjects() {
  if (selectForm.value.importAs === ImportAs.FINDINGS) {
    const findings = parsedData.value.filter(f => selectForm.value.selected.includes(f.id)) as PentestFinding[];
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
