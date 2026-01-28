<template>
  <v-container fluid class="pa-4">
    <v-row>
      <v-col cols="12">
        <h1>Export to Jira</h1>
        <p class="text-body-1 mt-2">
          Export selected findings from {{ project.name }} to Jira as issues.
        </p>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="6">
        <s-select
          v-model="selectedJiraProject"
          label="Jira Project"
          :items="jiraProjects"
          item-title="name"
          item-value="id"
          :loading="loadingProjects"
          :disabled="loadingProjects"
          @update:model-value="onJiraProjectChange"
          hint="Select the Jira project to export findings to"
          persistent-hint
        >
          <template #item="{ item, props }">
            <v-list-item 
              :title="item.raw.name" 
              :subtitle="item.raw.key" 
              v-bind="props"
            />
          </template>
        </s-select>
      </v-col>

      <v-col cols="12" md="6">
        <s-select
          v-model="selectedIssueType"
          label="Issue Type"
          :items="issueTypes"
          item-title="name"
          item-value="id"
          :loading="loadingIssueTypes"
          :disabled="!selectedJiraProject || loadingIssueTypes"
          hint="Select the type of issue to create (e.g., Bug, Task)"
          persistent-hint
        />
      </v-col>
    </v-row>

    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>Select Findings to Export</v-card-title>
          <v-card-text>
            <v-list
              v-model:selected="selectedFindings"
              select-strategy="leaf"
              density="compact"
              class="finding-list"
            >
              <v-list-item
                v-for="finding in findings"
                :key="finding.id"
                :value="finding"
                :class="`finding-level-${riskLevel(finding)}`"
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
                  <v-list-item-title class="text-body-2">
                    {{ finding.data.title || 'Untitled Finding' }}
                  </v-list-item-title>
                </template>
              </v-list-item>
              <v-list-item v-if="findings.length === 0">
                <v-list-item-title>No findings in this project</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-4">
      <v-col cols="12">
        <s-btn-primary
          @click="exportToJira"
          :loading="exporting"
          :disabled="!canExport"
          prepend-icon="mdi-export"
          text="Export to Jira"
        >
          <template #loader>
            <s-saving-loader-spinner />
            Exporting...
          </template>
        </s-btn-primary>
        <span v-if="selectedFindings.length > 0" class="ml-4 text-body-2">
          {{ selectedFindings.length }} finding(s) selected
        </span>
      </v-col>
    </v-row>

    <!-- Export Results Dialog -->
    <s-dialog v-model="showResultsDialog" max-width="800">
      <template #title>Export Results</template>
      <template #default>
        <v-card-text>
          <v-alert
            v-if="exportResults.success.length > 0"
            type="success"
            class="mb-4"
          >
            Successfully created {{ exportResults.success.length }} issue(s) in Jira
          </v-alert>

          <v-alert
            v-if="exportResults.failed.length > 0"
            type="error"
            class="mb-4"
          >
            Failed to create {{ exportResults.failed.length }} issue(s)
          </v-alert>

          <div v-if="exportResults.success.length > 0">
            <h3 class="text-subtitle-1 mb-2">Created Issues:</h3>
            <v-list density="compact">
              <v-list-item
                v-for="issue in exportResults.success"
                :key="issue.jira_key"
                :title="getFindingTitle(issue.finding_id)"
                :subtitle="issue.jira_key"
                :href="issue.jira_url"
                target="_blank"
                prepend-icon="mdi-open-in-new"
              />
            </v-list>
          </div>

          <div v-if="exportResults.failed.length > 0" class="mt-4">
            <h3 class="text-subtitle-1 mb-2">Failed Issues:</h3>
            <v-list density="compact">
              <v-list-item
                v-for="issue in exportResults.failed"
                :key="issue.finding_id"
                :title="getFindingTitle(issue.finding_id)"
              >
                <v-list-item-subtitle class="text-error">
                  {{ issue.error }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </div>
        </v-card-text>
      </template>
    </s-dialog>
  </v-container>
</template>

<script setup lang="ts">
import {
  useFetchE,
  type PentestProject,
  type PentestFinding,
  type ProjectType,
} from '#imports';
import { getFindingRiskLevel, sortFindings } from '@base/utils/project';
import { findingToADF } from '@/utils/finding2adf';

interface JiraProject {
  id: string;
  key: string;
  name: string;
}

interface JiraIssueType {
  id: string;
  name: string;
}

interface ExportResults {
  success: Array<{ finding_id: string; jira_key: string; jira_url: string }>;
  failed: Array<{ finding_id: string; error: string }>;
}

const route = useRoute();
const appConfig = useAppConfig();

// Load project data
const project = await useFetchE<PentestProject & { findings: PentestFinding[] }>(
  `/api/v1/pentestprojects/${route.params.projectId}/`,
  { method: 'GET' }
);
const projectType = await useFetchE<ProjectType>(
  `/api/v1/projecttypes/${project.value.project_type}/`,
  { method: 'GET' }
);

const findings = computed(() =>
  sortFindings({
    findings: project.value.findings,
    projectType: projectType.value,
    overrideFindingOrder: project.value.override_finding_order,
  })
);

// Jira data
const jiraProjects = ref<JiraProject[]>([]);
const issueTypes = ref<JiraIssueType[]>([]);
const selectedJiraProject = ref<string>('');
const selectedIssueType = ref<string>('');
const selectedFindings = ref<PentestFinding[]>([...findings.value]);

// UI state
const loadingProjects = ref(false);
const loadingIssueTypes = ref(false);
const exporting = ref(false);
const showResultsDialog = ref(false);
const exportResults = ref<ExportResults>({
  success: [],
  failed: [],
});

const canExport = computed(() => {
  return (
    selectedJiraProject.value &&
    selectedIssueType.value &&
    selectedFindings.value.length > 0 &&
    !exporting.value
  );
});

// Load Jira projects on mount
onMounted(async () => {
  await loadJiraProjects();
});

async function loadJiraProjects() {
  loadingProjects.value = true;
  try {
    const response = await $fetch<{ projects: JiraProject[] }>(
      `/api/plugins/${appConfig.pluginId}/api/projects/${project.value.id}/jira/projects/`,
      { method: 'GET' }
    );
    jiraProjects.value = response.projects;
  } catch (error: any) {
    errorToast(`Failed to load Jira projects: ${error.message || error}`);
  } finally {
    loadingProjects.value = false;
  }

  if (jiraProjects.value.length > 0) {
    selectedJiraProject.value = jiraProjects.value[0]!.id;
    await onJiraProjectChange();
  }
}

async function onJiraProjectChange() {
  if (!selectedJiraProject.value) {
    issueTypes.value = [];
    selectedIssueType.value = '';
    return;
  }

  loadingIssueTypes.value = true;
  try {
    const response = await $fetch<{ issueTypes: JiraIssueType[] }>(
      `/api/plugins/${appConfig.pluginId}/api/projects/${project.value.id}/jira/issuetypes/`,
      { 
        method: 'GET', 
        query: {
          jira_project: selectedJiraProject.value 
        },
      }
    );
    issueTypes.value = response.issueTypes;
    
    // Auto-select first issue type if available
    if (issueTypes.value.length > 0) {
      selectedIssueType.value = issueTypes.value[0]!.id;
    }
  } catch (error: any) {
    errorToast(`Failed to load issue types: ${error.message || error}`);
  } finally {
    loadingIssueTypes.value = false;
  }
}

async function exportToJira() {
  if (!canExport.value) {
    return;
  }

  exporting.value = true;
  try {
    // Prepare issues data
    const issues = selectedFindings.value.map((finding) => {
      const adfDescription = findingToADF(finding, projectType.value);
      
      return {
        finding_id: finding.id,
        summary: finding.data.title || 'Untitled Finding',
        description: adfDescription,
      };
    });

    // Send to backend
    const response = await $fetch<ExportResults>(
      `/api/plugins/${appConfig.pluginId}/api/projects/${project.value.id}/jira/exportissues/`,
      {
        method: 'POST',
        body: {
          jira_project: selectedJiraProject.value,
          issue_type: selectedIssueType.value,
          issues,
        },
      }
    );

    exportResults.value = response;
    showResultsDialog.value = true;

    if (response.success.length > 0) {
      successToast(
        `Successfully exported ${response.success.length} finding(s) to Jira`
      );
    }
  } catch (error: any) {
    errorToast(`Export failed: ${error.message || error}`);
  } finally {
    exporting.value = false;
  }
}

function riskLevel(finding: PentestFinding) {
  return getFindingRiskLevel({ finding, projectType: projectType.value });
}

function getFindingTitle(findingId: string): string {
  const finding = findings.value.find(f => f.id === findingId);
  return finding?.data?.title || findingId;
}
</script>

<style lang="scss" scoped>
@use 'sass:map';
@use '@base/assets/settings' as settings;

@for $level from 1 through 5 {
  .finding-level-#{$level} {
    border-left: 0.4em solid map.get(settings.$risk-color-levels, $level);
  }
}

.finding-list {
  max-height: 500px;
  overflow-y: auto;
}
</style>
