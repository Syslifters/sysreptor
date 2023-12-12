<template>
  <full-height-page>
    <s-sub-drawer>
      <v-list-item :to="`/designs/${$route.params.projectTypeId}/`" exact prepend-icon="mdi-cogs" title="Settings">
        <s-tooltip activator="parent" text="Settings" />
      </v-list-item>
      <v-list-item :to="`/designs/${$route.params.projectTypeId}/pdfdesigner/`" prepend-icon="mdi-pencil-ruler" title="PDF Designer">
        <s-tooltip activator="parent" text="PDF Designer" />
      </v-list-item>
      <v-list-item :to="`/designs/${$route.params.projectTypeId}/reportfields/`" prepend-icon="mdi-alpha-r-box" title="Report Fields">
        <s-tooltip activator="parent" text="Report Fields" />
      </v-list-item>
      <v-list-item :to="`/designs/${$route.params.projectTypeId}/findingfields/`" prepend-icon="mdi-alpha-f-box" title="Finding Fields">
        <s-tooltip activator="parent" text="Finding Fields" />
      </v-list-item>
    </s-sub-drawer>

    <nuxt-page />
  </full-height-page>
</template>

<script setup lang="ts">
const route = useRoute();
const projectTypeStore = useProjectTypeStore();

await useAsyncDataE(async () => await projectTypeStore.getById(route.params.projectTypeId as string), { key: 'projectTypeMenu:projectType' });
const projectType = computed(() => projectTypeStore.projectType(route.params.projectTypeId as string));

useHeadExtended({
  titleTemplate: title => designTitleTemplate(projectType.value, title, route),
  breadcrumbs: () => designDetailBreadcrumbs(projectType.value),
});
</script>
