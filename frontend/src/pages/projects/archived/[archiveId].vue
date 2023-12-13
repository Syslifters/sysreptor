<template>
  <v-container class="pt-0">
    <edit-toolbar>
      <template #title>{{ archive.name }}</template>

      <s-dialog v-model="restoreWizard.visible">
        <template #activator="{ props: dialogProps }">
          <s-btn-primary
            :disabled="publicKeyEncryptedKeyParts.length === 0"
            prepend-icon="mdi-folder-lock-open-outline"
            text="Restore"
            v-bind="dialogProps"
          />
        </template>
        <template #title>Restore Project</template>

        <template #default>
          <split-menu :model-value="20">
            <template #menu>
              <v-list
                v-model:selected="restoreWizard.selectedParts"
                mandatory
                density="compact"
              >
                <v-list-subheader>Public Keys</v-list-subheader>
                <v-list-item
                  v-for="encryptedPart in publicKeyEncryptedKeyParts"
                  :key="encryptedPart.id"
                  :value="encryptedPart"
                  :title="encryptedPart.public_key.name"
                />
              </v-list>
            </template>
            <template #default>
              <v-container v-if="restoreWizard.selectedParts.length > 0" fluid>
                <p>
                  Decrypt the following message with your private key <strong>{{ restoreWizard.selectedParts[0].public_key.name }}</strong>
                  and copy the decrypted data into the text field below.
                </p>
                <p><s-code>gpg --decrypt message.txt</s-code></p>
                <v-textarea
                  v-model="restoreWizard.selectedParts[0].encrypted_data"
                  auto-grow
                  readonly
                  spellcheck="false"
                  class="textarea-codeblock pt-0"
                />

                <s-text-field
                  v-model="restoreWizard.form.data"
                  label="Decrypted data"
                  :error-messages="restoreWizard.error || []"
                  spellcheck="false"
                />
                <btn-confirm
                  :action="decryptKeyPart"
                  :disabled="!restoreWizard.form.data"
                  :confirm="false"
                  button-text="Restore"
                  button-icon="mdi-folder-lock-open-outline"
                  button-color="primary"
                  class="mt-4"
                />
              </v-container>
            </template>
          </split-menu>
        </template>
      </s-dialog>
    </edit-toolbar>

    <div class="mb-4">
      <chip-created :value="archive.created" />
      <chip-auto-delete :value="archive.auto_delete_date" />
      <chip-tag v-for="tag in archive.tags" :key="tag" :value="tag" />
    </div>

    <p class="mt-4">
      <strong>{{ archive.threshold }} of {{ archive.key_parts.length }}</strong> users are required to restore the project.<br>
      <template v-if="archive.key_parts.filter(p => p.is_decrypted).length > 0">
        <strong>{{ archive.threshold - archive.key_parts.filter(p => p.is_decrypted).length }} more users</strong> required to restore the project.<br>
        They have to decrypt their key parts {{ restoreUntilDate }},
        otherwise all decrypted key parts will be reset due to inactivity and archive restoring has to start again.
      </template>
    </p>

    <h6 class="text-h6 mt-4">Users</h6>
    <v-table>
      <tbody>
        <tr v-for="keypart in archive.key_parts" :key="keypart.id">
          <td>
            {{ keypart.user.username }}<template v-if="keypart.user.name"> ({{ keypart.user.name }})</template>
            <v-chip v-if="!keypart.user.is_active" size="small" class="ml-4" color="warning">
              <v-icon size="small" start icon="mdi-alert" />
              inactive
            </v-chip>
          </td>
          <td>
            <template v-if="keypart.is_decrypted">
              <v-icon color="success" icon="mdi-lock-open-variant" />
              Restored at {{ formatISO9075(parseISO(keypart.decrypted_at!)) }}
            </template>
            <template v-else>
              <v-icon color="error" icon="mdi-lock" />
              Encrypted
            </template>
          </td>
        </tr>
      </tbody>
    </v-table>
  </v-container>
</template>

<script setup lang="ts">
import { formatDistanceToNowStrict, formatISO9075, isSameDay, parseISO } from "date-fns";

const route = useRoute();
const auth = useAuth();

const archive = await useFetchE<ArchivedProject>(`/api/v1/archivedprojects/${route.params.archiveId}/`, { method: 'GET' });
const userKeyPart = computed(() => archive.value.key_parts.find(keypart => keypart.user.id === auth.user.value!.id));
const publicKeyEncryptedKeyParts = await useAsyncDataE(async () => {
  if (userKeyPart.value && !userKeyPart.value.is_decrypted) {
    return await $fetch<ArchivedProjectPublicKeyEncryptedKeyPart[]>(`/api/v1/archivedprojects/${route.params.archiveId}/keyparts/${userKeyPart.value.id}/public-key-encrypted-data/`, { method: 'GET' });
  }
  return [];
});
const restoreUntilDate = computed(() => {
  if (!archive.value.reencrypt_key_parts_after_inactivity_date) {
    return null;
  }
  const date = parseISO(archive.value.reencrypt_key_parts_after_inactivity_date);
  if (isSameDay(date, new Date()) || date <= new Date()) {
    return 'today';
  }

  return 'in the next ' + formatDistanceToNowStrict(date, { unit: 'day' });
})

useHeadExtended({
  title: archive.value.name,
  breadcrumbs: () => archivedProjectDetailBreadcrumbs(archive.value),
});

const restoreWizard = ref({
  visible: false,
  selectedParts: publicKeyEncryptedKeyParts.value.length > 0 ? [publicKeyEncryptedKeyParts.value[0]] : [],
  form: {
    data: '',
  },
  error: null as string[]|null,
});

async function decryptKeyPart() {
  if (!userKeyPart.value) {
    return;
  }

  try {
    const res = await $fetch<{status: string, project_id: string|null}>(`/api/v1/archivedprojects/${archive.value.id}/keyparts/${userKeyPart.value.id}/decrypt/`, {
      method: 'POST',
      body: restoreWizard.value.form,
    });
    restoreWizard.value.visible = false;
    if (res.status === 'project-restored') {
      successToast('Project restored successfully.');
      await navigateTo(`/projects/${res.project_id}/`)
    } else {
      successToast('Key part decrypted successfully. More users are required to restore the project.');
      await refreshNuxtData();
    }
  } catch (error: any) {
    if (error?.status === 400 && error?.data?.[0]) {
      restoreWizard.value.error = error.data;
    }
  }
}

</script>

<style lang="scss" scoped>
@use "@/assets/vuetify.scss" as vuetify;

.textarea-codeblock {
  :deep(textarea) {
    font-family: monospace;
    line-height: 1.2em;
    font-size: medium;
    background-color: vuetify.$code-background-color;
    color: vuetify.$code-color;
  }
}
</style>
