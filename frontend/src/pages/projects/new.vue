<template>
  <v-container fluid class="pt-0">
    <v-form ref="formRef" @submit.prevent="performCreate">
      <edit-toolbar :form="formRef">
        <template #title>Create new Project</template>
        <template #default>
          <s-btn-primary 
            type="submit"
            text="Create"
            prepend-icon="mdi-content-save"
          />
        </template>
      </edit-toolbar>

      <s-text-field 
        v-model="projectForm.name" 
        label="Name" 
        :error-messages="serverErrors?.name || []"
        spellcheck="false" 
        class="mt-4" 
      />
      <s-project-type-selection 
        v-model="projectForm.project_type" 
        :error-messages="serverErrors?.project_type || []"
        class="mt-4" 
      />
      <s-member-selection 
        v-model="projectForm.members" 
        :prevent-unselecting-self="true" 
        :required="true" 
        :error-messages="serverErrors?.members || []"
        class="mt-4" 
      />
      <s-tags 
        v-model="projectForm.tags" 
        :error-messages="serverErrors?.tags || []"
        class="mt-4" 
      />
    </v-form>
  </v-container>
</template>

<script setup lang="ts">
import type { VForm } from "vuetify/lib/components/index.mjs";

useHeadExtended({
  title: 'Projects',
  breadcrumbs: () => projectListBreadcrumbs().concat([{ title: 'New', to: '/projects/new/' }]),
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
const serverErrors = ref<any|null>(null);

const formRef = ref<VForm>();
async function performCreate() {
  const { valid } = await formRef.value!.validate();
  if (!valid) {
    return;
  }

  try {
    const project = await projectStore.createProject(projectForm.value);
    await navigateTo(`/projects/${project.id}/reporting/`);
  } catch (error: any) {
    if (error?.status === 400 && error?.data) {
      serverErrors.value = error.data;
    }
    requestErrorToast({ error });
  }
}
</script>
