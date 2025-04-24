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
                  { value: RenderFindingsMode.COMBINED, title: 'Combined (all findings in one PDF)'}, 
                  { value: RenderFindingsMode.SEPARATE, title: 'Separate (each finding in a separate PDF)' }
                ]"
              />
            </v-col>
          </v-row>
          <div>
            <v-btn 
              href="https://github.com/Syslifters/sysreptor/tree/main/plugins/renderfindings/README.md" 
              target="_blank"
              text="The PDF does not look right? You might need to update your design."
              prepend-icon="mdi-help-circle" 
              variant="plain" 
              density="compact"
              class="btn-help"
            />
          </div>

          <p class="mt-2">
            Select all findings that should be included in the PDF.
          </p>
        </div>

        <v-list
          v-model:selected="selectedFindings"
          select-strategy="leaf"
          density="compact"
          class="flex-grow-1 overflow-y-auto"
        >
          <v-list-item
            v-for="finding in findings" :key="finding.id"
            :value="finding"
            :class="`finding-level-${riskLevel(finding)}`"
          >
            <template #prepend="{ isSelected }">
              <v-list-item-action start>
                <v-checkbox-btn 
                  :model-value="isSelected" 
                  density="compact"
                />
              </v-list-item-action>
            </template>
            <template #default>
              <v-list-item-title class="text-body-2">{{ finding.data.title }}</v-list-item-title>
            </template>
          </v-list-item>
          <v-list-item v-if="project.findings.length === 0"
            title="No findings yet"
          />
        </v-list>
      </div>
    </template>
  </split-menu>
</template>

<script setup lang="ts">
import { useFetchE, type PentestProject, type PentestFinding, type PdfResponse, MessageLevel, type ProjectType, type ErrorMessage } from '#imports';
import type { PdfPreview } from '#components';
import { getFindingRiskLevel, sortFindings } from '@base/utils/project';
import { base64decode, fileDownload } from '@base/utils/helpers';

enum RenderFindingsMode {
  COMBINED = 'combined',
  SEPARATE = 'separate',
}

const route = useRoute();
const appConfig = useAppConfig();

const project = await useFetchE<PentestProject & { findings: PentestFinding[] }>(`/api/v1/pentestprojects/${route.params.projectId}/`, { method: 'GET'});
const projectType = await useFetchE<ProjectType>(`/api/v1/projecttypes/${project.value.project_type}/`, { method: 'GET' });
const findings = computed(() => sortFindings({
  findings: project.value.findings,
  projectType: projectType.value,
  overrideFindingOrder: project.value.override_finding_order,
}));
const selectedFindings = ref<PentestFinding[]>([]);
const renderMode = ref<RenderFindingsMode>(RenderFindingsMode.COMBINED);

const menuSize = ref(50);
const pdfPreviewRef = useTemplateRef<typeof PdfPreview>('pdfPreviewRef');
const renderingInProgress = computed(() => pdfPreviewRef.value?.renderingInProgress);
function refreshPdfPreview() {
  if (renderingInProgress.value) {
    return;
  }

  pdfPreviewRef.value?.reloadImmediate();
}

async function fetchPreviewPdf(fetchOptions: { signal: AbortSignal }): Promise<PdfResponse> {
  let findingIds = selectedFindings.value.map(f => f.id);
  if (findingIds.length === 0) {
    return {
      pdf: null,
      messages: [{
        level: MessageLevel.INFO,
        message: 'Select one or more findings.',
      }],
      timings: {},
    };
  }

  const res = await $fetch<PdfResponse>(`/api/plugins/${appConfig.pluginId}/api/projects/${project.value.id}/renderfindings/`, {
    method: 'POST',
    body: {
      finding_ids: renderMode.value == RenderFindingsMode.SEPARATE ? [findingIds[0]] : findingIds,
    },
    ...fetchOptions,
  });

  if (res.pdf) {
    // close warnings panel on successfuly render
    pdfPreviewRef.value.showMessages = false;
  }

  return res;
}

async function downloadPdf() {
  if (renderMode.value === RenderFindingsMode.COMBINED) {
    if (!pdfPreviewRef.value?.pdfData) {
      return;
    }

    fileDownload(base64decode(pdfPreviewRef.value.pdfData), 'finding.pdf');
  } else {
    // Get findings in order of list
    const findingsToRender = findings.value.filter(f => selectedFindings.value.includes(f));
    for (let i = 0; i < findingsToRender.length; i++) {
      selectedFindings.value = [findingsToRender[i]!];
      pdfPreviewRef.value.reloadImmediate();
      
      // wait until rendered
      while (renderingInProgress.value) {
        await wait(200);
      }
      
      const rateLimitMessage = (pdfPreviewRef.value?.messages || []).find((m: ErrorMessage) => m.details?.startsWith('Request was throttled'));
      const waitTime = rateLimitMessage?.details?.match(/available in (\d+) seconds/)?.[1];
      if (pdfPreviewRef.value) {
        // download PDF
        fileDownload(base64decode(pdfPreviewRef.value.pdfData), `finding-${i + 1}.pdf`);
      } else if (Number.isInteger(waitTime)) {
        // handle rate limit
        await wait((waitTime + 1) * 1000);
        i--;
      } else if (!pdfPreviewRef.value?.pdfData) {
        // rendering error
        errorToast(`Failed to render PDF for finding ${i + 1} "${findingsToRender[i]!.data.title}"`);
      }
    }
    selectedFindings.value = findingsToRender;
  }
}

function riskLevel(finding: PentestFinding) {
  return getFindingRiskLevel({ finding, projectType: projectType.value });
}
</script>

<style lang="scss" scoped>
@use 'sass:map';
@use "@base/assets/settings" as settings;

@for $level from 1 through 5 {
  .finding-level-#{$level} {
    border-left: 0.4em solid map.get(settings.$risk-color-levels, $level);
  }
}

.btn-help {
  text-transform: none;
  letter-spacing: normal;
}
</style>
