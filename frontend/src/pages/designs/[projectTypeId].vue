<template>
  <full-height-page>
    <template #header>
      <s-sub-menu>
        <v-tab :to="`/designs/${$route.params.projectTypeId}/`" exact text="General Settings" />
        <v-tab :to="`/designs/${$route.params.projectTypeId}/pdfdesigner/`" text="PDF Designer" />
        <v-tab :to="`/designs/${$route.params.projectTypeId}/reportfields/`" text="Report Fields" />
        <v-tab :to="`/designs/${$route.params.projectTypeId}/findingfields/`" text="Finding Fields" />
      </s-sub-menu>
    </template>

    <nuxt-page />
  </full-height-page>
</template>
