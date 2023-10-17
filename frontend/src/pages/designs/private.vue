<template>
  <file-drop-area @drop="importBtn.performImport($event)" class="h-100">
    <full-height-page>
      <template #header>
        <s-sub-menu v-if="apiSettings.settings!.features.private_designs">
          <v-tab to="/designs/" exact text="Global Designs" />
          <v-tab to="/designs/private/" text="Private Designs" />
        </s-sub-menu>
      </template>

      <list-view url="/api/v1/projecttypes/?scope=private&ordering=name">
        <template #title>Private Designs</template>
        <template #actions>
          <design-create-design-dialog project-type-scope="private" />
          <btn-import ref="importBtn" :import="performImport" class="ml-1 mr-1" />
        </template>
        <template #item="{item}">
          <v-list-item :to="`/designs/${item.id}/pdfdesigner/`" :title="item.name" />
        </template>
      </list-view>
    </full-height-page>
  </file-drop-area>
</template>

<script setup lang="ts">
import { uploadFileHelper } from "~/utils/upload";

definePageMeta({
  title: 'Private Designs',
});

const apiSettings = useApiSettings();
const importBtn = ref();

async function performImport(file: File) {
  const designs = await uploadFileHelper<ProjectType[]>('/api/v1/projecttypes/import/', file, { scope: ProjectTypeScope.USER });
  await navigateTo(`/designs/${designs[0].id}/`)
}
</script>
