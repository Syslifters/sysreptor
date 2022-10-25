<template>
  <div>
    <s-sub-menu>
      <v-tab :to="`/designer/${$route.params.projectTypeId}/`" exact>General Settings</v-tab>
      <v-tab :to="`/designer/${$route.params.projectTypeId}/pdfdesigner/`">PDF Designer</v-tab>
      <v-tab :to="`/designer/${$route.params.projectTypeId}/reportfields/`">Report Fields</v-tab>
      <v-tab :to="`/designer/${$route.params.projectTypeId}/findingfields/`">Finding Fields</v-tab>
    </s-sub-menu>
   
    <NuxtChild />
  </div>
</template>
