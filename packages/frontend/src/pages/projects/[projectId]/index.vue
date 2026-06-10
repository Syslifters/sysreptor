<template>
  <v-container class="pt-0">
    <v-form ref="formRef">
      <edit-toolbar v-bind="toolbarAttrs" ref="toolbarRef">
        <template #title>Project Settings</template>
        <template #default>
          <permission-info :value="auth.permissions.value.update_project_settings">
            <btn-readonly 
              :value="project.readonly" 
              :set-readonly="setReadonly" 
              :disabled="!auth.permissions.value.update_project_settings"
              :show-toast="true"
              :project="project"
              class="ml-1 mr-1" 
            />
          </permission-info>
          <permission-info :value="auth.permissions.value.archive_projects || !apiSettings.isProfessionalLicense" permission-name="Global Archiver">
            <s-btn-secondary
              v-if="project.readonly"
              :disabled="!auth.permissions.value.archive_projects"
              :to="`/projects/${project.id}/archive/`"
              class="mr-1"
              prepend-icon="mdi-folder-lock-outline"
            >
              <pro-info>Archive</pro-info>
            </s-btn-secondary>
          </permission-info>
          <btn-history v-model="historyVisible" />
        </template>
        <template #context-menu>
          <btn-copy
            :copy="performCopy"
            confirm-text="The whole project will be copied including all members, sections, findings and images."
            :disabled="!auth.permissions.value.create_projects"
          />
          <btn-export
            :export-url="`/api/v1/pentestprojects/${project.id}/export/`"
            :options="{ export_all: false }"
            :name="'project-' + project.name"
          />
          <btn-export
            :export-url="`/api/v1/pentestprojects/${project.id}/export/`"
            :options="{ export_all: true }"
            :name="'project-' + project.name"
            button-text="Export (with notes)"
          />
          <btn-customize-design
            :action="() => projectStore.customizeDesign(project)"
            :project="project"
            :project-type="projectType"
            button-variant="list-item"
          />
        </template>
      </edit-toolbar>

      <history-timeline-project
        v-model="historyVisible"
        :project="project"
        :current-url="route.fullPath"
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
        :readonly="readonly"
        spellcheck="false"
        class="mt-4"
      />

      <s-project-type-selection
        :model-value="projectType || project.project_type"
        @update:model-value="projectType = ($event as ProjectType|null)"
        :query-filters="{scope: [ProjectTypeScope.GLOBAL, ProjectTypeScope.PRIVATE, ProjectTypeScope.PROJECT], linked_project: project.id}"
        :error-messages="serverErrors?.project_type || []"
        :readonly="readonly || project.readonly"
        :append-link="true"
        :required="true"
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
        :readonly="readonly || project.readonly"
        class="mt-4"
      />
      <s-tags
        v-model="project.tags"
        :items="tagSuggestions.getTags"
        :error-messages="serverErrors?.tags || []"
        :readonly="readonly"
        class="mt-4"
      />
      <s-member-selection
        v-model="project.members"
        :error-messages="serverErrors?.members || []"
        :readonly="readonly"
        :required="true"
        label="Members"
        class="mt-4"
      />
      <s-member-selection
        v-if="project.imported_members.length > 0"
        v-model="project.imported_members"
        :selectable-users="project.imported_members"
        :error-messages="serverErrors?.imported_members || []"
        :readonly="readonly"
        :disable-add="true"
        label="Members (imported)"
        hint="These users do not exist on this instance, they were imported from somewhere else. They do not have access, but can be included in reports."
        class="mt-4"
      />
      <s-date-picker
        v-if="project.readonly || project.delete_date || wasDeleteDateSet"
        v-model="project.delete_date"
        :allow-never="true"
        :min-date="formatISO9075(new Date(), { representation: 'date' })"
        hint="Date when this project will be automatically deleted. Select Never to disable automatic deletion, or clear the field to unset."
        :error-messages="serverErrors?.delete_date || []"
        :readonly="readonly || !apiSettings.isProfessionalLicense"
        class="mt-4"
      >
        <template #label><pro-info>Delete Date</pro-info></template>
      </s-date-picker>
      <v-alert v-if="deleteDateWarning" type="warning" class="mt-2">
        {{ deleteDateWarning }}
      </v-alert>
    </v-form>
  </v-container>
</template>

<script setup lang="ts">
import type { VForm } from "vuetify/lib/components/index.mjs";
import { formatDistanceToNowStrict, formatISO9075, isSameDay, parseISO } from 'date-fns';
import { isDeleteDateSoon } from '@base/utils/project';
import { ProjectTypeScope } from '#imports';

const route = useRoute();
const auth = useAuth();
const apiSettings = useApiSettings();
const projectStore = useProjectStore();
const projectTypeStore = useProjectTypeStore();
const tagSuggestions = useProjectTags();

const project = await useFetchE<PentestProject>(`/api/v1/pentestprojects/${route.params.projectId}/`, { method: 'GET', deep: true });
const serverErrors = ref<any|null>(null);
const projectType = ref<ProjectType|null>(null);
const historyVisible = ref(false);

const formRef = useTemplateRef<VForm>('formRef');
const toolbarRef = useTemplateRef<ToolbarRef['value']>('toolbarRef');

const { toolbarAttrs, readonly, editMode } = useLockEdit<PentestProject>({
  toolbarRef,
  data: project,
  form: formRef,
  hasEditPermissions: computed(() => {
    if (!auth.permissions.value.update_project_settings) {
      return false;
    }
    return true;
  }),
  canDelete: computed(() => auth.permissions.value.delete_projects),
  performSave: async () => {
    try {
      project.value = await projectStore.partialUpdateProject(project.value,
        ['name', 'project_type', 'force_change_project_type', 'language', 'tags', 'members', 'imported_members', 'delete_date']);
      serverErrors.value = null;
      projectType.value = await projectTypeStore.getById(project.value.project_type);
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

const wasDeleteDateSet = ref(false);
whenever(() => project.value.delete_date, () => { wasDeleteDateSet.value = true }, { immediate: true });
const deleteDateWarning = computed(() => {
  if (
    !project.value.readonly || 
    !apiSettings.isProfessionalLicense || 
    !isDeleteDateSoon(project.value.delete_date)
  ) {
    return null;
  }
  const date = parseISO(project.value.delete_date!);
  let formattedDate = formatDistanceToNowStrict(date, { unit: 'day' });
  if (isSameDay(date, new Date()) || date <= new Date()) {
    formattedDate = 'today';
  }
  return `This project will be automatically deleted in ${formattedDate}.`;
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
async function performCopy(data?: object) {
  const obj = await projectStore.copyProject({ ...project.value, ...data });
  await toolbarRef.value?.resetComponent();
  await navigateTo(`/projects/${obj.id}/`);
}

</script>
