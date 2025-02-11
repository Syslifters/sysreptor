<template>
  <full-height-page>
    <s-sub-drawer>
      <template #default="{ isExpanded }" v-if="project">
        <v-list-item :to="`/projects/${project.id}/`" exact prepend-icon="mdi-cogs" title="Settings" data-testid="project-settings-tab">
          <s-tooltip v-if="!isExpanded" activator="parent" text="Project Settings" />
        </v-list-item>
        <v-list-item :to="`/projects/${project.id}/notes/`" prepend-icon="mdi-notebook" title="Notes" data-testid="project-notes-tab">
          <s-tooltip v-if="!isExpanded" activator="parent" text="Notes" />
        </v-list-item>
        <v-list-item :to="`/projects/${project.id}/reporting/`" prepend-icon="mdi-text" title="Reporting" data-testid="project-reporting-tab">
          <s-tooltip v-if="!isExpanded" activator="parent" text="Reporting" />
        </v-list-item>
        <v-list-item :to="`/projects/${project.id}/designer/`" v-if="projectType?.source === 'customized'" prepend-icon="mdi-pencil-ruler" title="Designer" data-testid="project-designer-tab">
          <s-tooltip v-if="!isExpanded" activator="parent" text="Designer" />
        </v-list-item>
        <v-list-item :to="`/projects/${project.id}/publish/`" prepend-icon="mdi-earth" title="Publish" data-testid="project-publish-tab">
          <s-tooltip v-if="!isExpanded" activator="parent" text="Publish" />
        </v-list-item>
        <v-list-item :to="`/projects/${project.id}/history/`" prepend-icon="mdi-history" title="History" data-testid="project-history-tab">
          <s-tooltip v-if="!isExpanded" activator="parent" text="History" />
        </v-list-item>
        
        <template v-if="pluginMenuEntries.length > 0">
          <v-list-subheader>
            <span v-if="isExpanded">Plugins</span>
          </v-list-subheader>
          <v-list-item
            v-for="pluginMenuEntry, idx in pluginMenuEntries"
            :key="idx"
            :to="pluginUrl(pluginMenuEntry, { projectId: route.params.projectId })"
            :title="pluginMenuEntry.title"
            :prepend-icon="pluginMenuEntry.icon || 'mdi-puzzle'"
            v-bind="pluginMenuEntry.attrs"
          >
            <s-tooltip v-if="!isExpanded" activator="parent" :text="pluginMenuEntry.title" />
          </v-list-item>
        </template>
      </template>
    </s-sub-drawer>

    <nuxt-page />
  </full-height-page>
</template>

<script setup lang="ts">
import { projectTitleTemplate } from "#imports";

const route = useRoute();
const router = useRouter();
const pluginStore = usePluginStore();
const projectStore = useProjectStore();
const projectTypeStore = useProjectTypeStore();

await useAsyncDataE(async () => await projectStore.getById(route.params.projectId as string), { key: 'projectMenu:project' });
const project = computed(() => projectStore.project(route.params.projectId as string)!);
const projectType = await useAsyncDataE(async () => await projectTypeStore.getById(project.value.project_type), { key: 'projectMenu:projectType' });
watch(() => project.value?.project_type, async () => {
  if (!project.value) {
    return;
  }
  projectType.value = await projectTypeStore.getById(project.value.project_type);
});

const pluginMenuEntries = computed(() => pluginStore.menuEntriesForScope(PluginRouteScope.PROJECT));

useHeadExtended({
  titleTemplate: title => projectTitleTemplate(project.value, title, route),
  breadcrumbs: () => projectDetailBreadcrumbs(project.value),
});
</script>
