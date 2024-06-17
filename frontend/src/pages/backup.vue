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
      button-text="Create Backup"
      button-icon="mdi-download"
      button-color="primary"
      :disabled="!apiSettings.settings!.features.backup"
      class="mt-4"
    />
  </v-container>
</template>

<script setup lang="ts">
import fileDownload from "js-file-download";
import { formatISO } from 'date-fns';

definePageMeta({
  title: 'Backup',
  toplevel: true,
});
useHeadExtended({
  breadcrumbs: () => [{ title: 'Backup', to: '/backup/' }],
});

const route = useRoute();
const auth = useAuth();
const apiSettings = useApiSettings();

onBeforeMount(async () => {
  // Enable admin permissions
  if (apiSettings.isProfessionalLicense && auth.user.value?.is_superuser && !auth.permissions.value.admin) {
    await navigateTo({ path: '/users/self/admin/enable/', query: { next: route.fullPath } }, { replace: true });
  }
});

const backupKey = ref('');
const backupKeyError = ref<string|null>(null);
const rules = {
  backupKey: [
    (v: string) => !!v || 'Backup Key is required',
    (v: string) => v.length >= 20 || 'Backup Key must be at least 20 characters long',
  ],
}

async function createBackup() {
  try {
    backupKeyError.value = null;
    const backupBlob = await $fetch<Blob>('/api/v1/utils/backup/', {
      method: 'POST',
      body: { 
        key: backupKey.value 
      },
      responseType: "blob",
    });
    fileDownload(backupBlob, `backup-${formatISO(new Date())}.zip`);
    successToast('Backup successful');
  } catch (error: any) {
    const errorData = await new Promise<any>((resolve) => {
      if (error.data instanceof Blob && error.data.type === 'application/json') {
        const fr = new FileReader();
        fr.onload = () => {
          resolve(JSON.parse(fr.result as string) as any);
        };
        fr.onerror = () => {
          resolve(null);
        };
        fr.readAsText(error.data);
      } else {
        resolve(null);
      }
    });

    if (errorData?.detail || errorData?.key) {
      backupKeyError.value = errorData.detail || errorData.key;
    } else {
      throw error;
    }
  }
}
</script>
