<template>
  <v-container fluid class="pt-0">
    <v-form ref="formRef">
      <edit-toolbar v-bind="toolbarAttrs">
        <template #title>Project Settings</template>
        <template #default>
          <btn-readonly 
            :value="project.readonly" 
            :set-readonly="setReadonly" 
            :disabled="!auth.permissions.update_project_settings"
            class="ml-1 mr-1" 
          />
          <s-btn-secondary
            v-if="project.readonly"
            :disabled="!auth.permissions.archive_projects"
            :to="`/projects/${project.id}/archive/`"
            class="mr-1"
            prepend-icon="mdi-folder-lock-outline"
          >
            <pro-info>Archive</pro-info>
          </s-btn-secondary>
          <btn-history v-model="historyVisible" />
        </template>
        <template #context-menu>
          <btn-copy
            :copy="performCopy"
            confirm-text="The whole project will be copied including all members, sections, findings and images."
            :disabled="!auth.permissions.create_projects"
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
        :disabled="readonly"
        spellcheck="false"
        class="mt-4"
      />

      <s-project-type-selection
        :model-value="projectType || project.project_type"
        @update:model-value="projectType = $event"
        :query-filters="{scope: [ProjectTypeScope.GLOBAL, ProjectTypeScope.PRIVATE, ProjectTypeScope.PROJECT], linked_project: project.id}"
        :error-messages="serverErrors?.project_type || []"
        :disabled="readonly"
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
              tooltip-text="Duplicate project and change design in the duplicated project"
              confirm-text="The whole project will be copied including all sections, findings, images, etc. All changes are made in the duplicated project. No data will be lost."
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
        :disabled="readonly"
        class="mt-4"
      />
      <s-tags
        v-model="project.tags"
        :error-messages="serverErrors?.tags || []"
        :disabled="readonly"
        class="mt-4"
      />
      <s-member-selection
        v-model="project.members"
        :error-messages="serverErrors?.members || []"
        :disabled="readonly"
        :required="true"
        label="Members"
        class="mt-4"
      />
      <s-member-selection
        v-if="project.imported_members.length > 0"
        v-model="project.imported_members"
        :selectable-users="project.imported_members"
        :error-messages="serverErrors?.imported_members || []"
        :disabled="readonly"
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

const route = useRoute();
const auth = useAuth();
const projectStore = useProjectStore();

const project = await useFetchE<PentestProject>(`/api/v1/pentestprojects/${route.params.projectId}/`, { method: 'GET', key: 'projectSettings:project' });
const serverErrors = ref<any|null>(null);
const projectType = ref(null);
const historyVisible = ref(false);

const formRef = ref<VForm>();
const toolbarRef = ref();
const { toolbarAttrs, readonly, editMode } = useLockEdit<PentestProject>({
  data: project,
  form: formRef,
  hasEditPermissions: computed(() => {
    if (project.value?.readonly) {
      return false;
    } else if (auth.permissions.update_project_settings) {
      return false;
    }
    return true;
  }),
  canDelete: computed(() => auth.permissions.delete_projects),
  errorMessage: computed(() => {
    if (project.value?.readonly) {
      return 'This project is finished and cannot be changed anymore. In order to edit this project, re-activate it in the project settings.'
    }
    return null;
  }),
  performSave: async () => {
    try {
      project.value = await projectStore.partialUpdateProject(project.value,
        ['name', 'project_type', 'force_change_project_type', 'language', 'tags', 'members', 'imported_members']);
      serverErrors.value = null;
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
  deleteConfirmInput: computed(() => project.value.name),
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
    await refreshNuxtData();
  } finally {
    delete p.force_change_project_type;
  }
}

async function setReadonly(val: boolean) {
  await projectStore.setReadonly(project.value, val);
  await toolbarRef.value?.resetComponent();
  await refreshNuxtData();
  if (!val) {
    editMode.value = EditMode.EDIT;
  }
}
async function performCopy(data?: Object) {
  const obj = await projectStore.copyProject({ ...project.value, ...data });
  await toolbarRef.value?.resetComponent();
  await navigateTo(`/projects/${obj.id}/`);
}

</script>
