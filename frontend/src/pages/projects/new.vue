<template>
  <v-container class="pt-0">
    <v-form ref="formRef" @submit.prevent="performCreate">
      <edit-toolbar :form="formRef" :save="performCreate" save-button-text="Create">
        <template #title>Create new Project</template>
      </edit-toolbar>

      <s-text-field v-model="projectForm.name" label="Name" spellcheck="false" class="mt-4" />
      <s-project-type-selection v-model="projectForm.project_type" class="mt-4" />
      <s-member-selection v-model="projectForm.members" :prevent-unselecting-self="true" :required="true" class="mt-4" />
      <s-tags v-model="projectForm.tags" class="mt-4" />
    </v-form>
  </v-container>
</template>

<script setup lang="ts">
import type { VForm } from "vuetify/lib/components/index.mjs";
import { ProjectMember } from "~/utils/types";

definePageMeta({
  title: 'Projects',
});

const auth = useAuth();
const apiSettings = useApiSettings();
const projectStore = useProjectStore();

const projectForm = ref({
  name: '',
  project_type: null,
  tags: [] as string[],
  members: [{
    ...auth.user.value!,
    roles: apiSettings.settings!.project_member_roles.filter(r => r.default).map(r => r.role),
  }] as ProjectMember[],
});

const formRef = ref<VForm>();
async function performCreate() {
  const { valid } = await formRef.value!.validate();
  if (!valid) {
    return;
  }

  try {
    const project = await projectStore.createProject(projectForm.value);
    await navigateTo(`/projects/${project.id}/reporting/`);
  } catch (error) {
    requestErrorToast({ error });
  }
}
</script>
