<template>
  <file-drop-area @drop="importBtnRef.performImport($event)" class="h-100">
    <list-view url="/api/v1/projecttypes/?scope=private&ordering=name">
      <template #title>Designs</template>
      <template #actions>
        <design-create-design-dialog />
        <design-import-design-dialog ref="importBtnRef" />
      </template>
      <template #tabs>
        <v-tab :to="{ path: '/designs/', query: route.query }" exact prepend-icon="mdi-earth" text="Global Designs" />
        <v-tab :to="{ path: '/designs/private/', query: route.query }" prepend-icon="mdi-account" text="Private Designs" />
      </template>
      <template #item="{item}">
        <v-list-item :to="`/designs/${item.id}/pdfdesigner/`" :title="item.name" />
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

const importBtnRef = ref();
</script>
