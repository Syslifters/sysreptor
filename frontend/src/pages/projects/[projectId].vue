<template>
  <full-height-page>
    <template #header>
      <s-sub-menu v-if="project">
        <v-tab :to="`/projects/${project.id}/`" exact text="Project" />
        <v-tab :to="`/projects/${project.id}/notes/`" text="Notes" />
        <v-tab :to="`/projects/${project.id}/reporting/`" text="Reporting" />
        <v-tab :to="`/projects/${project.id}/publish/`" text="Publish" />
        <v-tab :to="`/projects/${project.id}/designer/`" v-if="projectType?.source === 'customized'" text="Designer" />
      </s-sub-menu>
    </template>

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

useHead({
  titleTemplate: title => projectTitleTemplate(project.value, title, route),
});
</script>
