<template>
  <file-drop-area @drop="importBtnRef.performImport($event)" class="h-100">
    <list-view url="/api/v1/projecttypes/?scope=global&ordering=name">
      <template #title>Designs</template>
      <template #actions>
        <design-create-design-dialog :project-type-scope="ProjectTypeScope.GLOBAL" />
        <design-import-design-dialog ref="importBtnRef" :project-type-scope="ProjectTypeScope.GLOBAL" />
      </template>
      <template #tabs v-if="apiSettings.settings!.features.private_designs">
        <v-tab :to="{ path: '/designs/', query: route.query }" exact prepend-icon="mdi-earth" text="Global" />
        <v-tab :to="{ path: '/designs/private/', query: route.query }" prepend-icon="mdi-account" text="Private" />
      </template>
      <template #item="{item}: {item: ProjectType}">
        <design-list-item :item="item" />
      </template>
    </list-view>
  </file-drop-area>
</template>

<script setup lang="ts">
definePageMeta({
  title: 'Designs',
  toplevel: true,
});
useHeadExtended({
  breadcrumbs: () => designListBreadcrumbs(),
});

const route = useRoute();
const apiSettings = useApiSettings();

const importBtnRef = ref();
</script>
