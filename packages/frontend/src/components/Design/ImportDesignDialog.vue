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

async function performImport(file: File) {
  const designs = await uploadFileHelper<ProjectType[]>('/api/v1/projecttypes/import/', file, { scope: props.projectTypeScope });
  await navigateTo(`/designs/${designs[0]!.id}/`)
}

const importBtnRef = useTemplateRef('importBtnRef');
defineExpose({
  performImport: (files?: FileList|File[]|null) => importBtnRef.value?.performImport(files),
});
</script>
