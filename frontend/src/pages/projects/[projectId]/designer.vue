<template>
  <split-menu v-model="previewSplitSize" :content-props="{ class: 'h-100 pa-0' }">
    <template #menu>
      <full-height-page>
        <template #header>
          <edit-toolbar v-bind="toolbarAttrs">
            <template #title>{{ project.name }}</template>

            <template #default>
              <s-btn-secondary
                :loading="pdfRenderingInProgress"
                :disabled="pdfRenderingInProgress"
                @click="loadPdf"
                prepend-icon="mdi-cached"
                text="Refresh PDF"
              >
                <template #loader>
                  <s-saving-loader-spinner />
                  Refresh PDF
                </template>
              </s-btn-secondary>
            </template>
          </edit-toolbar>

          <v-tabs v-model="currentTab" grow>
            <v-tab :value="PdfDesignerTab.HTML" text="HTML+Vue" />
            <v-tab :value="PdfDesignerTab.CSS" text="CSS" />
            <v-tab :value="PdfDesignerTab.ASSETS" text="Assets" />
          </v-tabs>
        </template>

        <v-window v-model="currentTab" class="h-100">
          <v-window-item :value="PdfDesignerTab.HTML" class="h-100">
            <design-code-editor
              ref="htmlEditor"
              v-model="projectType.report_template"
              language="html"
              class="h-100"
              :disabled="readonly"
            />
          </v-window-item>
          <v-window-item :value="PdfDesignerTab.CSS" class="h-100">
            <design-code-editor
              ref="cssEditor"
              v-model="projectType.report_styles"
              language="css"
              class="h-100"
              :disabled="readonly"
            />
          </v-window-item>
          <v-window-item :value="PdfDesignerTab.ASSETS" class="h-100 overflow-y-auto">
            <design-asset-manager :project-type="projectType" :disabled="readonly" />
          </v-window-item>
        </v-window>
      </full-height-page>
    </template>

    <template #default>
      <!-- PDF preview -->
      <pdf-preview
        ref="pdfPreviewRef"
        :fetch-pdf="fetchPdf"
      />
    </template>
  </split-menu>
</template>

<script setup lang="ts">
import pick from "lodash/pick";
import { PdfDesignerTab } from "~/utils/types";

const route = useRoute();
const projectStore = useProjectStore();

const currentTab = ref(PdfDesignerTab.HTML);
const previewSplitSize = ref(60);

const pdfPreviewRef = ref();
const htmlEditor = ref();
const cssEditor = ref();

const pdfRenderingInProgress = computed(() => pdfPreviewRef.value?.renderingInProgress);

const project = await useAsyncDataE(async () => await projectStore.getById(route.params.projectId as string), { key: 'projectdesigner:project' })
const { projectType, toolbarAttrs, readonly } = useProjectTypeLockEdit({
  ...await useProjectTypeLockEditOptions({
    id: project.value.project_type,
    save: true,
    saveFields: ['report_template', 'report_styles', 'report_preview_data'],
  }),
  hasEditPermissions: computed(() => !project.value.readonly),
  errorMessage: computed(() => project.value.readonly ? 
    'This project is finished and cannot be changed anymore. In order to edit this project, re-activate it in the project settings.' : 
    null),
});

async function fetchPdf() {
  return await $fetch<PdfResponse>(`/api/v1/pentestprojects/${project.value.id}/preview/`, {
    method: 'POST',
    body: pick(projectType.value, ['report_template', 'report_styles']),
  });
}
function loadPdf(immediate = true) {
  if (immediate) {
    pdfPreviewRef.value.reloadImmediate();
  } else {
    pdfPreviewRef.value.reloadDebounced();
  }
}
watch(projectType, () => loadPdf(false), { deep: true })
</script>
