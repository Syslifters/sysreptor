<template>
  <full-height-page>
    <s-sub-drawer>
      <template v-if="project">
        <v-list-item :to="`/projects/${project.id}/`" exact prepend-icon="mdi-cogs" title="Settings">
          <s-tooltip activator="parent" text="Project Settings" />
        </v-list-item>
        <v-list-item :to="`/projects/${project.id}/notes/`" prepend-icon="mdi-notebook" title="Notes">
          <s-tooltip activator="parent" text="Notes" />
        </v-list-item>
        <v-list-item :to="`/projects/${project.id}/reporting/`" prepend-icon="mdi-text" title="Reporting">
          <s-tooltip activator="parent" text="Reporting" />
        </v-list-item>
        <v-list-item :to="`/projects/${project.id}/designer/`" v-if="projectType?.source === 'customized'" prepend-icon="mdi-pencil-ruler" title="Designer">
          <s-tooltip activator="parent" text="Designer" />
        </v-list-item>
        <v-list-item :to="`/projects/${project.id}/publish/`" prepend-icon="mdi-earth" title="Publish">
          <s-tooltip activator="parent" text="Publish" />
        </v-list-item>
        <v-list-item :to="`/projects/${project.id}/history/`" prepend-icon="mdi-history" title="History">
          <s-tooltip activator="parent" text="History" />
        </v-list-item>
      </template>
    </s-sub-drawer>

    <nuxt-page />
  </full-height-page>
</template>

<script setup lang="ts">
import { projectTitleTemplate } from "~/utils/title";

const route = useRoute();
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

useHeadExtended({
  titleTemplate: title => projectTitleTemplate(project.value, title, route),
  breadcrumbs: () => projectDetailBreadcrumbs(project.value),
});
</script>
