<template>
  <div>
    <s-sub-menu>
      <v-tab :to="`/projects/${$route.params.projectId}/project/`">Project</v-tab>
      <v-tab :to="`/projects/${$route.params.projectId}/reporting/`">Reporting</v-tab>
      <v-tab :to="`/projects/${$route.params.projectId}/publish/`">Publish</v-tab>
    </s-sub-menu>

    <NuxtChild />
  </div>
</template>
