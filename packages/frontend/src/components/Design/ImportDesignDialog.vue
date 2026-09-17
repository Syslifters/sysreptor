<template>
  <permission-info :value="canImport" :permission-name="props.projectTypeScope === ProjectTypeScope.GLOBAL ? 'Designer' : undefined">
    <btn-import 
      ref="importBtnRef"
      :import="performImport" 
      :disabled="!canImport"
    />
  </permission-info>
</template>

<script setup lang="ts">
import { ProjectTypeScope } from "#imports";

const props = defineProps<{
  projectTypeScope?: ProjectTypeScope
}>();

const auth = useAuth();
const canImport = computed(() => {
  if (props.projectTypeScope === ProjectTypeScope.GLOBAL) {
    return auth.permissions.value.designer;
  } else {
    return auth.permissions.value.private_designs;
  }
});

async function performImport(files: File[]) {
  const results = await bulkAction(
    files,
    file => uploadFileHelper<ProjectType[]>('/api/v1/projecttypes/import/', file, { scope: props.projectTypeScope }),
    f => `Import failed for "${f.name}"`,
  );
  const imported = results.find(r => r)?.[0];
  if (!imported) {
    return;
  }
  await navigateTo(`/designs/${imported.id}/`);
}

const importBtnRef = useTemplateRef('importBtnRef');
defineExpose({
  performImport: (files?: FileList|File[]|null) => importBtnRef.value?.performImport(files),
});
</script>
