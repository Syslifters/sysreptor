<template>
  <div>
    <s-sub-menu>
      <v-tab :to="`/designer/${$route.params.projectTypeId}/`" nuxt exact>General Settings</v-tab>
      <v-tab :to="`/designer/${$route.params.projectTypeId}/pdfdesigner/`" nuxt>PDF Designer</v-tab>
      <v-tab :to="`/designer/${$route.params.projectTypeId}/reportfields/`" nuxt>Report Fields</v-tab>
      <v-tab :to="`/designer/${$route.params.projectTypeId}/findingfields/`" nuxt>Finding Fields</v-tab>
    </s-sub-menu>
   
    <NuxtChild />
  </div>
</template>
