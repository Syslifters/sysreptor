<template>
  <v-container class="pt-0">
    <v-form ref="formRef">
      <edit-toolbar v-bind="toolbarAttrs">
        <template #title>Project</template>
        <template #default>
          <s-btn @click="historyVisible = !historyVisible" color="secondary" prepend-icon="mdi-history">
            <span class="d-none d-lg-inline">Version History</span>
          </s-btn>
          <btn-readonly :value="project.readonly" :set-readonly="setReadonly" class="ml-1 mr-1" />
          <s-btn
            v-if="project.readonly && apiSettings.settings!.features.archiving"
            :to="`/projects/${project.id}/archive/`"
            color="secondary"
            class="mr-1"
            prepend-icon="mdi-folder-lock-outline"
            text="Archive"
          />
        </template>
        <template #context-menu>
          <btn-copy
            :copy="performCopy"
            tooltip-text="Duplicate Project"
            confirm-text="The whole project will be copied including all members, sections, findings and images."
          />
          <btn-export
            :export-url="`/api/v1/pentestprojects/${project.id}/export/`"
            :name="'project-' + project.name"
          />
          <btn-export
            :export-url="`/api/v1/pentestprojects/${project.id}/export/all/`"
            :name="'project-' + project.name"
            button-text="Export (with notes)"
          />
        </template>
      </edit-toolbar>

      <project-history-timeline
        v-model="historyVisible"
        :project="project"
        :current-url="$route.fullPath"
      />

      <p v-if="project.copy_of" class="mt-4">
        This project is a copy
        <s-btn
          :to="`/projects/${project.copy_of}/reporting/`"
          variant="text"
          size="small"
          prepend-icon="mdi-chevron-right-circle-outline"
          text="show original"
          class="ml-1 mr-1"
        />
      </p>

      <s-text-field
        v-model="project.name"
        label="Name"
        :error-messages="serverErrors?.name || []"
        :disabled="project.readonly"
        spellcheck="false"
        class="mt-4"
      />

      <s-project-type-selection
        :model-value="projectType || project.project_type"
        @update:model-value="projectType = $event"
        :query-filters="{scope: [ProjectTypeScope.GLOBAL, ProjectTypeScope.PRIVATE, ProjectTypeScope.PROJECT], linked_project: project.id}"
        :error-messages="serverErrors?.project_type || []"
        :disabled="project.readonly"
        :append-link="true"
        return-object
        class="mt-4"
      >
        <template #message="{message}">
          {{ message }}
          <template v-if="message === 'Designs have incompatible field definitions. Converting might result in data loss.'">
            <btn-confirm
              :action="forceChangeDesign"
              button-text="Force change"
              button-color="error"
              tooltip-text="Force change Design"
              dialog-text="Force change the Design for this project. WARNING: Data of incompatible fields might get lost."
              color="error"
              variant="text"
              size="x-small"
            />
            <btn-copy
              :copy="() => performCopy({project_type: project.project_type})"
              button-text="Duplicate"
              tooltip-text="Duplicate Project and change Design"
              confirm-text="The whole project will be copied including all sections, findings and images. All changes are made in the duplicated project. No data will be lost."
              button-variant="default"
              color="inherit"
              variant="text"
              size="x-small"
              :button-icon="null"
            />
          </template>
        </template>
      </s-project-type-selection>

      <s-language-selection
        v-model="project.language"
        :error-messages="serverErrors?.language || []"
        :disabled="project.readonly"
        class="mt-4"
      />
      <s-tags
        v-model="project.tags"
        :error-messages="serverErrors?.tags || []"
        :disabled="project.readonly"
        class="mt-4"
      />
      <s-member-selection
        v-model="project.members"
        :error-messages="serverErrors?.members || []"
        :disabled="project.readonly"
        :required="true"
        label="Members"
        class="mt-4"
      />
      <s-member-selection
        v-if="project.imported_members.length > 0"
        v-model="project.imported_members"
        :selectable-users="project.imported_members"
        :error-messages="serverErrors?.imported_members || []"
        :disabled="project.readonly"
        :disable-add="true"
        label="Members (imported)"
        hint="These users do not exist on this instance, they were imported from somewhere else. They do not have access, but can be included in reports."
        class="mt-4"
      />
    </v-form>
  </v-container>
</template>

<script setup lang="ts">
import type { VForm } from "vuetify/lib/components/index.mjs";
import { PentestProject, ProjectType } from "~/utils/types";

const route = useRoute();
const apiSettings = useApiSettings();
const projectStore = useProjectStore();

const project = await useFetchE<PentestProject>(`/api/v1/pentestprojects/${route.params.projectId}/`, { method: 'GET' });
const serverErrors = ref<any|null>(null);
const projectType = ref(null);
const deleteConfirmInput = computed(() => project.value.name);
const historyVisible = ref(false);

const toolbarRef = ref();
const formRef = ref<VForm>();
const { toolbarAttrs } = useLockEdit<PentestProject>({
  data: project,
  form: formRef,
  ...(!project.value.readonly ? {
    performSave: async () => {
      try {
        project.value = await projectStore.partialUpdateProject(project.value,
          ['name', 'project_type', 'force_change_project_type', 'language', 'tags', 'members', 'imported_members']);
      } catch (error: any) {
        if (error?.status === 400 && error?.data) {
          serverErrors.value = error.data;
        }
        throw error;
      }
    },
    performDelete: async () => {
      await projectStore.deleteProject(project.value);
      await navigateTo('/projects/');
    },
    deleteConfirmInput,
  } : {}),
});

watch(projectType, (val: ProjectType|null) => {
  if (val) {
    project.value.project_type = val.id;
  }
});

async function forceChangeDesign() {
  const p = project.value as PentestProject & { force_change_project_type?: boolean};
  try {
    p.force_change_project_type = true;
    await toolbarRef.value?.performSave();
    serverErrors.value = null;
    delete p.force_change_project_type;
    await toolbarRef.value?.resetComponent();
    window.location.reload();
  } finally {
    delete p.force_change_project_type;
  }
}

async function setReadonly(val: boolean) {
  await projectStore.setReadonly(project.value, val);
  await toolbarRef.value?.resetComponent();
  window.location.reload();
}
async function performCopy(data?: Object) {
  const obj = await projectStore.copyProject({ ...project.value, ...data });
  await toolbarRef.value?.resetComponent();
  await navigateTo(`/projects/${obj.id}/`);
}

</script>
