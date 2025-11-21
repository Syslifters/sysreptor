<template>
  <split-menu v-model="menuSize">
    <template #menu>
      <pdf-preview
        ref="pdfPreviewRef"
        :fetch-pdf="fetchPreviewPdf"
        :show-loading-spinner-on-reload="true"
      />
    </template>

    <template #default>
      <h1>{{ project.name }}</h1>

      <v-form>
        <div class="mt-2">
          <s-btn-secondary
            :loading="checksOrPreviewInProgress"
            :disabled="checksOrPreviewInProgress"
            @click="refreshPreviewAndChecks"
            prepend-icon="mdi-cached"
            text="Refresh PDF"
            class="mr-1 mb-1"
          >
            <template #loader>
              <s-saving-loader-spinner />
              Refresh PDF
            </template>
          </s-btn-secondary>
          
          <btn-customize-design
            :action="() => projectStore.customizeDesign(project)"
            :project="project"
            :project-type="projectType"
            class="mr-1 mb-1"
          />
        </div>

        <!-- Filename -->
        <div class="mt-4">
          <s-text-field
            v-model="generatePdfForm.filename"
            label="Filename"
            :rules="rules.filename"
            spellcheck="false"
          />
        </div>

        <!-- PDF encryption password -->
        <div class="mt-4">
          <s-text-field
            v-model="generatePdfForm.password"
            label="PDF password (optional)"
            append-inner-icon="mdi-lock-reset" @click:append-inner="generatePdfForm.password = generateRandomPassword()"
            spellcheck="false"
          >
            <template #prepend>
              <s-checkbox v-model="shouldEncryptPdf" v-tooltip:top="'Encrypt PDF'" />
            </template>
          </s-text-field>
        </div>

        <div id="publish-actions-download" class="mt-4">
          <btn-confirm
            :disabled="!canGenerateFinalReport"
            :action="generateFinalReport.run"
            :confirm="false"
            button-text="Download"
            button-icon="mdi-download"
            button-color="primary-bg"
            class="mr-1 mb-1"
          />
          <s-dialog
            v-model="shareReportForm.dialogVisible"
            :min-width="mdAndDown ? '90vw' : '60vw'"
            min-height="50vh"
          >
            <template #activator="{ props: dialogProps }">
              <s-btn-primary
                prepend-icon="mdi-share-variant"
                text="Share by Link"
                :disabled="!canGenerateFinalReport || !auth.permissions.value.share_notes || !auth.permissions.value.edit_projects"
                :loading="shareReport.pending.value"
                class="mr-1 mb-1"
                v-bind="dialogProps"
              />
            </template>
            <template #title>Share Report by Link</template>
            <template #default>
              <v-card-text>
                <notes-share-info-form
                  v-model="shareReportForm.data"
                  :error="shareReportForm.error"
                  :hidden-fields="['permissions_write', 'is_revoked']"
                >
                  <template #header>
                    <p>Share report to allow public access via a share link.</p>
                  </template>
                  <template #append-fields>
                    <!-- Set password for encrypting report -->
                    <v-col cols="6">
                      <s-text-field
                        v-model="generatePdfForm.password"
                        label="PDF password (optional)"
                        append-inner-icon="mdi-lock-reset" @click:append-inner="generatePdfForm.password = generateRandomPassword()"
                        spellcheck="false"
                        class="mt-4"
                      >
                        <template #prepend>
                          <s-checkbox v-model="shouldEncryptPdf" />
                        </template>
                      </s-text-field>
                    </v-col>
                  </template>
                </notes-share-info-form>
              </v-card-text>
              <v-card-actions>
                <v-spacer />
                <s-btn-other
                  @click="shareReportForm.dialogVisible = false"
                  text="Cancel"
                />
                <btn-confirm
                  :action="shareReport.run"
                  :confirm="false"
                  button-icon="mdi-share-variant"
                  button-text="Share"
                  button-color="primary-bg"
                />
              </v-card-actions>
            </template>
          </s-dialog>
        </div>
      </v-form>

      <div class="mt-4">
        <v-list-subheader>Warnings</v-list-subheader>
        <v-divider />
        <error-list v-if="checkMessagesStatus !== 'pending'" :value="allMessages" :group="true" :show-no-message-info="true">
          <template #location="{msg}">
            <NuxtLink v-if="messageLocationUrl(msg) && msg.location" :to="messageLocationUrl(msg)" @click="onBeforeOpenMessageLocationUrl(msg)" target="_blank" class="text-primary">
              in {{ msg.location.type }}
              <span v-if="msg.location.name"> "{{ msg.location.name }}"</span>
              <span v-if="msg.location.path"> field "{{ msg.location.path }}"</span>
            </NuxtLink>
            <span v-else-if="msg.location?.name">
              in {{ msg.location.type }}
              <span v-if="msg.location.name"> "{{ msg.location.name }}"</span>
              <span v-if="msg.location.path"> field "{{ msg.location.path }}"</span>
            </span>
          </template>
        </error-list>
        <div v-else class="text-center pa-6">
          <v-progress-circular indeterminate />
        </div>
      </div>
    </template>
  </split-menu>
</template>

<script setup lang="ts">
import type { PdfPreview } from "#components";
import { fileDownload, generateRandomPassword } from "@base/utils/helpers";
import { addDays, formatISO9075 } from "date-fns";

definePageMeta({
  title: 'Publish',
});

const route = useRoute();
const auth = useAuth();
const localSettings = useLocalSettings();
const projectStore = useProjectStore();
const projectTypeStore = useProjectTypeStore();
const { mdAndDown } = useDisplay();

const project = await useAsyncDataE(async () => await projectStore.getById(route.params.projectId as string));
const projectType = await useAsyncDataE(async () => await projectTypeStore.getById(project.value.project_type));

const { data: checkMessages, status: checkMessagesStatus, refresh: refreshCheckMessages } = useLazyFetch<{ messages: ErrorMessage[] }>(`/api/v1/pentestprojects/${project.value.id}/check/`, { method: 'GET' });
const pdfPreviewRef = useTemplateRef<InstanceType<typeof PdfPreview>>('pdfPreviewRef');
const allMessages = computed(() => {
  const out = [] as ErrorMessage[];
  if (checkMessages.value?.messages) {
    out.push(...checkMessages.value.messages);
  }
  if (pdfPreviewRef.value?.messages) {
    out.push(...pdfPreviewRef.value.messages);
  }
  if (checkMessagesStatus.value === 'error') {
    out.push({
      level: MessageLevel.ERROR,
      message: 'Error while checking project',
    });
  }
  return out;
});
const hasErrors = computed(() => allMessages.value.some(m => m.level === MessageLevel.ERROR));

const generatePdfForm = ref({
  password: localSettings.pdfPasswordEnabled ? generateRandomPassword() : '',
  filename: (project.value.name + '_report.pdf').replaceAll(/[\\/]/g, '').replaceAll(/\s+/g, ' '),
});
const shouldEncryptPdf = computed({
  get: () => !!generatePdfForm.value.password,
  set: (value) => { generatePdfForm.value.password = value ? generateRandomPassword() : '' }
});
watch(shouldEncryptPdf, () => {
  localSettings.pdfPasswordEnabled = shouldEncryptPdf.value;
});

const shareReportForm = ref({
  data: {
    expire_date: formatISO9075(addDays(new Date(), 14), { representation: 'date' }),
    permissions_write: false,
    is_revoked: false,
  } as ShareInfo,
  error: null as any|null,
  dialogVisible: false,
})
const rules = {
  filename: [(v: string) => (Boolean(v) && /^[^/\\]+$/.test(v)) || 'Invalid filename'],
}

const menuSize = ref(window.innerWidth * 0.6);
const checksOrPreviewInProgress = computed(() => checkMessagesStatus.value === 'pending' || pdfPreviewRef.value?.renderingInProgress);
const canGenerateFinalReport = computed(() => {
  return !hasErrors.value &&
        !checksOrPreviewInProgress.value &&
        pdfPreviewRef.value?.pdfData !== null;
});

function refreshPreviewAndChecks() {
  if (checksOrPreviewInProgress.value) {
    return;
  }

  pdfPreviewRef.value?.reloadImmediate();
  refreshCheckMessages();
}
async function fetchPreviewPdf(fetchOptions: { signal: AbortSignal }) {
  return await $fetch<PdfResponse>(`/api/v1/pentestprojects/${project.value.id}/preview/`, {
    method: 'POST',
    body: {},
    ...fetchOptions,
  });
}

async function generatePdfRequest(fetchOptions: { signal: AbortSignal }) {
  return await $fetch<Blob>(`/api/v1/pentestprojects/${project.value.id}/generate/`, {
    method: 'POST',
    body: {
      password: generatePdfForm.value.password,
    },
    responseType: 'blob',
    ...fetchOptions,
  });
}
const generateFinalReport = useAbortController(async (fetchOptions: { signal: AbortSignal }) => {
  const res = await generatePdfRequest(fetchOptions);
  fileDownload(res, generatePdfForm.value.filename + (generatePdfForm.value.filename.toLowerCase().endsWith('.pdf') ? '' : '.pdf'));
});
const shareReport = useAbortController(async (fetchOptions: { signal: AbortSignal }) => {
  try {
    const reportPdf = await generatePdfRequest(fetchOptions);
    const filename = generatePdfForm.value.filename + (generatePdfForm.value.filename.toLowerCase().endsWith('.pdf') ? '' : '.pdf')
    const uploadedFile = await uploadFileHelper<UploadedFileInfo>(`/api/v1/pentestprojects/${project.value.id}/upload/`, new File([reportPdf], filename), {}, fetchOptions);
    const note = await projectStore.createNote(project.value, {
      title: 'Report',
      icon_emoji: '📄',
      text: `[${uploadedFile.name}](/files/name/${uploadedFile.name})`,
      parent: null,
      order: 1,
    });
    await $fetch(`/api/v1/pentestprojects/${project.value.id}/notes/${note.id}/shareinfos/`, {
      method: 'POST',
      body: shareReportForm.value.data,
    });
    await navigateTo(`/projects/${project.value.id}/notes/${note.id}/#shareinfo`);
  } catch (error: any) {
    requestErrorToast({ error });
  }
})


function messageLocationUrl(msg: ErrorMessage) {
  if (!msg || !msg.location) {
    return undefined;
  } else if (msg.location.type === 'section') {
    return `/projects/${project.value.id}/reporting/sections/${msg.location.id}/` + (msg.location.path ? '#' + msg.location.path : '');
  } else if (msg.location.type === 'finding') {
    return `/projects/${project.value.id}/reporting/findings/${msg.location.id}/` + (msg.location.path ? '#' + msg.location.path : '');
  } else if (msg.location.type === 'design') {
    return `/designs/${project.value.project_type}/pdfdesigner/`;
  }

  return undefined;
}

function onBeforeOpenMessageLocationUrl(msg: ErrorMessage) {
  if (msg.message.includes('comment')) {
    // Open comment sidebar
    localSettings.reportingCommentSidebarVisible = true;
    localSettings.reportingCommentStatusFilter = CommentStatus.OPEN;
    localSettings.$persist();
  }
}

</script>

