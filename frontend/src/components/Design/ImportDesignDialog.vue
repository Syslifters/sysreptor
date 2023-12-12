<template>
  <span>
    <btn-import 
      ref="importBtnRef"
      :import="startImport" 
      :loading="actionInProgress"
      :disabled="!canImport"
      class="ml-1 mr-1" 
    />

    <s-dialog v-model="dialogVisible">
      <template #title>Import Design</template>
      <template #default>
        <v-card-text>
          <s-text-field
            :model-value="currentFile?.name"
            label="File"
            prepend-inner-icon="mdi-file"
            disabled
          />

          <s-select 
            v-model="currentScope"
            :items="scopeItems"
            label="Scope"
            class="mt-4"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <s-btn-other
            @click="dialogVisible = false"
            text="Cancel"
          />
          <s-btn-primary 
            @click="performImport"
            :loading="actionInProgress"
            prepend-icon="mdi-upload"
            text="Import"
          />
        </v-card-actions>
      </template>
    </s-dialog>
  </span>
</template>

<script setup lang="ts">
import { ProjectTypeScope } from "~/utils/types";

const auth = useAuth();
const apiSettings = useApiSettings();

const scopeItems = computed(() => {
  return [
    { value: ProjectTypeScope.GLOBAL, title: 'Global Design', props: { subtitle: 'Available for all users', disabled: !auth.hasScope('designer') } },
    { value: ProjectTypeScope.PRIVATE, title: 'Private Design', props: { subtitle: 'Available only for you', disabled: !apiSettings.settings?.features.private_designs } },
  ];
});
const currentScope = ref<ProjectTypeScope>(scopeItems.value.find(item => !item.props.disabled)?.value || ProjectTypeScope.GLOBAL);
const canImport = computed(() => scopeItems.value.some(item => !item.props.disabled));

const currentFile = ref<File|null>(null);
const dialogVisible = ref(false);
const actionInProgress = ref(false);

function startImport(file: File) {
  currentFile.value = file;
  dialogVisible.value = true;
}

async function performImport() {
  try {
    actionInProgress.value = true;
    const designs = await uploadFileHelper<ProjectType[]>('/api/v1/projecttypes/import/', currentFile.value!, { scope: currentScope.value });
    await navigateTo(`/designs/${designs[0].id}/`)
  } catch (error: any) {
    let message = 'Import failed';
    if (error?.status === 400 && error?.data?.format) {
      message += ': ' + error.data.format[0];
    }
    requestErrorToast({ error, message });
  } finally {
    dialogVisible.value = false;
    actionInProgress.value = false;
  }
}

const importBtnRef = ref();
defineExpose({
  performImport: (files?: FileList|null) => importBtnRef.value?.performImport(files),
});
</script>
