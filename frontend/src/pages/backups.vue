<template>
  <v-container class="h-100 overflow-y-auto">
    <h1>Backup</h1>

    <p v-if="!apiSettings.settings!.features.backup">
      No backup key configured. <br><br>
      You need to configure a <v-code tag="span">BACKUP_KEY</v-code> as environment variable. 
      This backup key has to be at least 20 characters long. 
      If no <v-code tag="span">BACKUP_KEY</v-code> is configured, the backup API endpoint is disabled.
    </p>
    <p v-else>
      Enter the configured <v-code tag="span">BACKUP_KEY</v-code> to create a backup of this SysReptor instance.
    </p>

    <s-password-field
      v-model="backupKey"
      label="Backup Key"
      :rules="rules.backupKey"
      :error-messages="backupKeyError"
      :hide-details="false"
      :disabled="!apiSettings.settings!.features.backup"
      class="mt-4"
    />
    <btn-confirm
      :action="createBackup"
      :confirm="false"
      button-text="Download Backup"
      button-icon="mdi-download"
      button-color="primary"
      :disabled="!apiSettings.settings!.features.backup"
      class="mt-2"
    />
    <form 
      v-if="renderDownloadForm" 
      ref="downloadForm"
      action="/api/v1/utils/backup/"
      method="POST"
      target="_blank"
    >
      <input type="hidden" name="key" :value="backupKey" />
      <input type="hidden" name="csrfmiddlewaretoken" :value="csrftoken" />
    </form>

    <s-card title="Backup History" class="mt-8">
      <template #text>
        <v-table>
          <thead>
            <tr>
              <th>Date</th>
              <th>User</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in backupLogs.data.value" :key="log.id">
              <td><chip-date :value="log.created" /></td>
              <td>{{ log.user || '-' }}</td>
              <td>
                <template v-if="log.type === BackupLogType.SETUP">Set up SysReptor instance</template>
                <template v-else-if="log.type === BackupLogType.BACKUP">Backup created</template>
                <template v-else-if="log.type === BackupLogType.RESTORE">Restored backup</template>
                <template v-else>{{ log.type }}</template>
              </td>
            </tr>
          </tbody>
        </v-table>
        <page-loader :items="backupLogs" />
      </template>
    </s-card>
  </v-container>
</template>

<script setup lang="ts">
import fileDownload from "js-file-download";
import { formatISO } from 'date-fns';
import { BackupLogType } from '@/utils/types';

definePageMeta({
  title: 'Backup',
  toplevel: true,
});
useHeadExtended({
  breadcrumbs: () => [{ title: 'Backup', to: '/backups/' }],
});

const auth = useAuth();
const csrftoken = useCookie('csrftoken');
const apiSettings = useApiSettings();

await useAsyncDataE(async () => {
  if (!auth.permissions.value.view_backup) {
    await navigateTo('/');
  }
});

const backupLogs = useSearchableCursorPaginationFetcher<BackupLog>({
  baseURL: '/api/v1/utils/backuplogs/',
});

const backupKey = ref('');
const backupKeyError = ref<string|null>(null);
const rules = {
  backupKey: [
    (v: string) => !!v || 'Backup Key is required',
    (v: string) => v.length >= 20 || 'Backup Key must be at least 20 characters long',
  ],
}

const renderDownloadForm = ref(false);
const downloadForm = ref<HTMLFormElement>();
async function createBackup() {
  try {
    // Check permissions and backup key
    // for error handling in frontend
    backupKeyError.value = null;
    await $fetch.raw('/api/v1/utils/backup/', {
      method: 'POST',
      body: { 
        key: backupKey.value,
        check: true,
      },
    });
    
    // Download backup via native browser mechanisms
    renderDownloadForm.value = true;
    await nextTick();
    downloadForm.value?.submit();
    await nextTick()
    renderDownloadForm.value = false;
  } catch (error: any) {
    console.log({ error });
    backupKeyError.value = error.data?.detail || error.data?.key;
    if (!backupKeyError.value) {
      throw error;
    }
  }
}
</script>
