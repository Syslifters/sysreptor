<template>
  <div class="h-100">
    <split-menu v-model="previewSplitSize" :content-props="{ class: 'h-100 pa-0' }">
      <template #menu>
        <full-height-page>
          <template #header>
            <edit-toolbar v-bind="toolbarAttrs">
              <template #title>{{ formatProjectTypeTitle(projectType) }}</template>

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
              <v-tab :value="PdfDesignerTab.LAYOUT" text="Layout" prepend-icon="mdi-flask" />
              <v-tab :value="PdfDesignerTab.HTML" text="HTML+Vue" />
              <v-tab :value="PdfDesignerTab.CSS" text="CSS" />
              <v-tab :value="PdfDesignerTab.ASSETS" text="Assets" />
              <v-tab :value="PdfDesignerTab.PREVIEW_DATA" text="Preview Data" />
            </v-tabs>
          </template>

          <v-window v-model="currentTab" class="h-100">
            <v-window-item :value="PdfDesignerTab.LAYOUT" class="h-100">
              <design-layout-editor
                :project-type="projectType"
                :disabled="readonly"
                @update="onUpdateCode"
                @jump-to-code="jumpToCode"
              />
            </v-window-item>
            <v-window-item :value="PdfDesignerTab.HTML" class="h-100">
              <design-code-editor
                ref="htmlEditor"
                v-model="projectType.report_template"
                language="html"
                class="h-100"
                :readonly="readonly"
              />
            </v-window-item>
            <v-window-item :value="PdfDesignerTab.CSS" class="h-100">
              <design-code-editor
                ref="cssEditor"
                v-model="projectType.report_styles"
                language="css"
                class="h-100"
                :readonly="readonly"
              />
            </v-window-item>
            <v-window-item :value="PdfDesignerTab.ASSETS" class="h-100 overflow-y-auto">
              <design-asset-manager :project-type="projectType" :disabled="readonly" />
            </v-window-item>
            <v-window-item :value="PdfDesignerTab.PREVIEW_DATA" class="h-100">
              <design-preview-data-form
                v-model="projectType.report_preview_data"
                :project-type="projectType"
                :upload-file="uploadFile"
                :rewrite-file-url="rewriteFileUrl"
                :readonly="readonly"
              />
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

    <s-dialog v-model="showStartDialog">
      <template #title>Start Designing</template>
      <template #default>
        <v-card-text>
          <p>
            It looks like you haven't started designing your report yet.
            We recommend following approach:
          </p>
          <ol class="ml-6 mt-2">
            <li>
              Before starting to design, define your
              <nuxt-link :to="`/designs/${projectType.id}/reportfields/`">report fields</nuxt-link> and
              <nuxt-link :to="`/designs/${projectType.id}/findingfields/`">finding fields</nuxt-link>
            </li>
            <li>Include base styles (click "Start Designing" below to add them)</li>
            <li>Define the report structure in "Layout"</li>
            <li>Customize the HTML and CSS to your needs via the code editors</li>
            <li>Hint: Use "Preview Data" to test your design</li>
          </ol>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <s-btn-other @click="showStartDialog = false" text="Cancel" />
          <s-btn-primary @click="startDesigning" text="Start Designing" />
        </v-card-actions>
      </template>
    </s-dialog>
  </div>
</template>

<script setup lang="ts">
import urlJoin from "url-join";
import { initialCss } from '~/components/Design/designer-components';
import { formatProjectTypeTitle, uploadFileHelper, PdfDesignerTab } from "#imports";

const currentTab = ref(PdfDesignerTab.HTML);
const previewSplitSize = ref(60);

const pdfPreviewRef = ref();
const htmlEditor = ref();
const cssEditor = ref();

const pdfRenderingInProgress = computed(() => pdfPreviewRef.value?.renderingInProgress);

const { projectType, toolbarAttrs, readonly } = useProjectTypeLockEdit(await useProjectTypeLockEditOptions({
  save: true,
  saveFields: ['report_template', 'report_styles', 'report_preview_data', 'finding_fields', 'report_sections'],
}));

async function fetchPdf() {
  return await $fetch<PdfResponse>(`/api/v1/projecttypes/${projectType.value.id}/preview/`, {
    method: 'POST',
    body: projectType.value
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

async function uploadFile(file: File) {
  const img = await uploadFileHelper<UploadedFileInfo>(`/api/v1/projecttypes/${projectType.value.id}/assets/`, file);
  return `![](/assets/name/${img.name}){width="auto"}`;
}
function rewriteFileUrl(imgSrc: string) {
  return urlJoin(`/api/v1/projecttypes/${projectType.value.id}/`, imgSrc);
}

const showStartDialog = ref(!projectType.value.report_template && !projectType.value.report_styles && !readonly.value);
function startDesigning() {
  showStartDialog.value = false;
  projectType.value.report_styles = initialCss;
  currentTab.value = PdfDesignerTab.LAYOUT;
}

async function onUpdateCode(options: { html: string, css: string, formatHtml?: boolean, reloadPdf?: boolean }) {
  projectType.value.report_template = options.html;
  projectType.value.report_styles = options.css;
  if (options.formatHtml) {
    await nextTick();
    htmlEditor.value?.formatDocument();
  }
  if (options.reloadPdf) {
    await nextTick();
    loadPdf(true);
  }
}
async function jumpToCode(options: { tab: PdfDesignerTab, position: DocumentSelectionPosition }) {
  currentTab.value = options.tab;
  await nextTick();
  await nextTick();

  if (options.tab === PdfDesignerTab.HTML) {
    htmlEditor.value?.jumpToPosition(options.position);
  } else if (options.tab === PdfDesignerTab.CSS) {
    cssEditor.value?.jumpToPosition(options.position);
  }
}
</script>
