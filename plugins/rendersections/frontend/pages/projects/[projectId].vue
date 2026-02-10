<template>
  <split-menu v-model="menuSize" :content-props="{ class: 'pa-0 h-100' }">
    <template #menu>
      <pdf-preview
        ref="pdfPreviewRef"
        :fetch-pdf="fetchPreviewPdf"
        :show-loading-spinner-on-reload="true"
      />
    </template>

    <template #default>
      <div class="h-100 d-flex flex-column">
        <div class="pa-2">
          <h1>{{ project.name }}</h1>
          <v-row>
            <v-col cols="auto">
              <s-btn-secondary
                :loading="renderingInProgress"
                :disabled="renderingInProgress"
                @click="refreshPdfPreview"
                prepend-icon="mdi-cached"
                text="Refresh PDF"
              >
                <template #loader>
                  <s-saving-loader-spinner />
                  Refresh PDF
                </template>
              </s-btn-secondary>
            </v-col>
            <v-col cols="auto">
              <s-btn-secondary
                @click="downloadPdf"
                :disabled="!pdfPreviewRef?.pdfData"
                prepend-icon="mdi-download"
                text="Download"
              />
            </v-col>
            <v-col cols="auto" class="flex-grow-1">
              <s-select
                v-model="renderMode"
                label="Render mode"
                :items="[
                  { value: RenderSectionsMode.COMBINED, title: 'Combined (all sections in one PDF)'},
                  { value: RenderSectionsMode.SEPARATE, title: 'Separate (each section in a separate PDF)' }
                ]"
              />
            </v-col>
          </v-row>
          <v-row>
              <v-col cols="auto" class="flex-grow-1">
                  <s-text-field
                    v-model="renderPassword"
                    label="PDF password (optional)"
                    append-inner-icon="mdi-lock-reset" @click:append-inner="renderPassword = generateRandomPassword()"
                    spellcheck="false"
                  >
                  </s-text-field>
              </v-col>
          </v-row>
          <div>
            <v-btn
              href="https://github.com/Syslifters/sysreptor/tree/main/plugins/rendersections/README.md"
              target="_blank"
              text="The PDF does not look right? You might need to update your design."
              prepend-icon="mdi-help-circle"
              variant="plain"
              density="compact"
              class="btn-help"
            />
          </div>

          <p class="mt-2">
            Select all sections that should be included in the PDF.
          </p>
        </div>

        <v-list
          v-model:selected="selectedSections"
          select-strategy="leaf"
          density="compact"
          class="flex-grow-1 overflow-y-auto"
        >
          <v-list-item v-if="loadingSections">
            <template #default>
              <div class="d-flex align-center gap-2">
                <v-progress-circular
                  indeterminate
                  size="20"
                  width="2"
                />
                <span class="text-body-2 ml-2">Loading sections...</span>
              </div>
            </template>
          </v-list-item>
          <v-list-item
            v-for="section in sections" :key="section.id"
            :value="section"
          >
            <template #prepend="{ isSelected, select }">
              <v-list-item-action start>
                <v-checkbox-btn
                  :model-value="isSelected"
                  @update:model-value="select"
                  density="compact"
                />
              </v-list-item-action>
            </template>
            <template #default>
              <v-list-item-title class="text-body-2">{{ section.name }}</v-list-item-title>
            </template>
          </v-list-item>
          <v-list-item v-if="!loadingSections && sections.length === 0"
            title="No sections yet"
          />
        </v-list>
      </div>
    </template>
  </split-menu>
</template>

<script setup lang="ts">
import { useFetchE, type PentestProject, type PentestFinding, type PdfResponse, MessageLevel, type ErrorMessage } from '#imports';
import type { PdfPreview } from '#components';
import { base64decode, fileDownload, generateRandomPassword } from '@base/utils/helpers';

enum RenderSectionsMode {
  COMBINED = 'combined',
  SEPARATE = 'separate',
}

const route = useRoute();
const appConfig = useAppConfig();

type Section = {
  id: string;
  name: string;
};

const project = await useFetchE<PentestProject & { findings: PentestFinding[] }>(`/api/v1/pentestprojects/${route.params.projectId}/`, { method: 'GET'});
const sections = ref<Section[]>([]);
const loadingSections = ref(true);
const selectedSections = ref<Section[]>([]);
const renderMode = ref<RenderSectionsMode>(RenderSectionsMode.COMBINED);
const renderPassword = ref<string>("");

const menuSize = ref(window.innerWidth * 0.5);

// Load sections asynchronously to avoid blocking page load
onMounted(async () => {
  try {
    sections.value = await $fetch<Section[]>(`/api/plugins/${appConfig.pluginId}/api/projects/${project.value.id}/sections/`, { method: 'GET' });
  } finally {
    loadingSections.value = false;
  }
});
const pdfPreviewRef = useTemplateRef<InstanceType<typeof PdfPreview>>('pdfPreviewRef');
const renderingInProgress = computed(() => pdfPreviewRef.value?.renderingInProgress);
function refreshPdfPreview() {
  if (renderingInProgress.value) {
    return;
  }

  pdfPreviewRef.value?.reloadImmediate();
}

async function fetchPreviewPdf(fetchOptions: { signal: AbortSignal }, allowEncrypt: boolean = false): Promise<PdfResponse> {
  let sectionIds = selectedSections.value.map(f => f.id);
  if (sectionIds.length === 0) {
    return {
      pdf: null,
      messages: [{
        level: MessageLevel.INFO,
        message: 'Select one or more sections.',
      }],
      timings: {},
    };
  }

  const res = await $fetch<PdfResponse>(`/api/plugins/${appConfig.pluginId}/api/projects/${project.value.id}/rendersections/`, {
    method: 'POST',
    body: {
      sections: renderMode.value == RenderSectionsMode.SEPARATE ? [sectionIds[0]] : sectionIds,
      pdf_password: allowEncrypt ? renderPassword.value : "",
    },
    ...fetchOptions,
  });

  if (res.pdf) {
    // close warnings panel on successfuly render
    pdfPreviewRef.value!.showMessages = false;
  }

  return res;
}

async function refreshAndDownloadPdf(filename: string) {
  pdfPreviewRef.value!.reloadImmediate();

  // wait until rendered
  while (renderingInProgress.value) {
    await wait(200);
  }
  const rateLimitMessage = (pdfPreviewRef.value?.messages || []).find((m: ErrorMessage) => m.details?.startsWith('Request was throttled'));
  const waitTime = rateLimitMessage?.details?.match(/available in (\d+) seconds/)?.[1];
  if (Number.isInteger(waitTime)) {
    // handle rate limit
    await wait((Number.parseInt(waitTime!) + 1) * 1000);
    return 'retry';
  } else if (pdfPreviewRef.value?.pdfData) {
    // download PDF
    fileDownload(base64decode(pdfPreviewRef.value.pdfData), filename);
    return 'success';
  } else {
    // rendering error
    return 'error';
  }
}

async function downloadPdf() {
  if (renderMode.value === RenderSectionsMode.COMBINED) {
    if (!pdfPreviewRef.value?.pdfData) {
      return;
    }

    while (true) {
      const res = await refreshAndDownloadPdf('section.pdf');
      if (res === 'error') {
        errorToast('Failed to render PDF');
        break;
      } else if (res === 'retry') {
        // retry
        continue;
      } else {
        // success
        break;
      }
    }
  } else {
    // Get sections in order of list
    const sectionsToRender = sections.value.filter(f => selectedSections.value.includes(f));
    for (let i = 0; i < sectionsToRender.length; i++) {
      selectedSections.value = [sectionsToRender[i]!];
      const res = await refreshAndDownloadPdf(`section-${i + 1}.pdf`);
      if (res === 'error') {
        errorToast(`Failed to render PDF for section ${i + 1} "${sectionsToRender[i]!.name}"`);
        break;
      } else if (res === 'retry') {
        // retry current section
        i--;
      } else {
        // success, continue with next section
      }
    }
    selectedSections.value = sectionsToRender;
  }
}
</script>

<style lang="scss" scoped>
@use 'sass:map';
@use "@base/assets/settings" as settings;

.btn-help {
  text-transform: none;
  letter-spacing: normal;
}
</style>
