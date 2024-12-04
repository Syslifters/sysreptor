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
          <s-btn-secondary
            :loading="renderingInProgress"
            :disabled="renderingInProgress"
            @click="refreshPdfPreview"
            prepend-icon="mdi-cached"
            text="Refresh PDF"
            class="mr-1 mb-1"
          >
            <template #loader>
              <s-saving-loader-spinner />
              Refresh PDF
            </template>
          </s-btn-secondary>
          <p>
            <v-btn 
              href="" 
              target="_blank"
              icon="mdi-help-circle" 
              variant="text" 
              density="compact"
            />
            <small>The PDF does not look right? </small>
          </p>

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
import { useFetchE, type PentestProject, type PentestFinding, type PdfResponse, MessageLevel, type ProjectType } from '#imports';
import { getFindingRiskLevel, sortFindings } from '@base/utils/project';

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

const menuSize = ref(50);
const pdfPreviewRef = ref();
const renderingInProgress = computed(() => pdfPreviewRef.value?.renderingInProgress);
function refreshPdfPreview() {
  if (renderingInProgress.value) {
    return;
  }

  pdfPreviewRef.value.reloadImmediate();
}

async function fetchPreviewPdf(fetchOptions: { signal: AbortSignal }): Promise<PdfResponse> {
  if (selectedFindings.value.length === 0) {
    return {
      pdf: null,
      messages: [{
        level: MessageLevel.INFO,
        message: 'Select one or more findings.',
      }],
      timings: {},
    };
  }

  const res = await $fetch<PdfResponse>(`/api/plugins/${appConfig.pluginId}/api/projects/${project.value.id}/renderfindingspdf/`, {
    method: 'POST',
    body: {
      finding_ids: selectedFindings.value.map(f => f.id),
    },
    ...fetchOptions,
  });

  if (res.pdf) {
    // close warnings panel on successfuly render
    console.log(pdfPreviewRef.value);
    pdfPreviewRef.value.showMessages = false;
  }

  return res;
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
</style>
