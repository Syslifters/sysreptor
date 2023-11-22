<template>
  <s-card class="mt-4">
    <v-card-title>SSO Identities</v-card-title>
    <v-card-text>
      <v-table>
        <thead>
          <tr>
            <th>SSO Provider</th>
            <th>Identifier</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in identities" :key="item.id">
            <td>{{ apiSettings.ssoAuthProviders.find(p => p.id === item.provider)?.name || item.provider }}</td>
            <td>{{ item.identifier }}</td>
            <td>
              <btn-delete button-variant="icon" :delete="() => deleteIdentity(item)" :disabled="!canEdit" />
            </td>
          </tr>
        </tbody>
      </v-table>

      <s-dialog v-model="createWizard.visible">
        <template #activator="{ props: dialogProps }">
          <s-btn
            v-bind="dialogProps"
            :disabled="!canEdit"
            color="secondary"
            prepend-icon="mdi-plus"
            text="Add"
          />
        </template>
        <template #title>Add Identity</template>
        <template #default>
          <v-card-text>
            <s-select
              v-model="createWizard.form.provider"
              label="SSO Provider"
              :items="apiSettings.ssoAuthProviders"
              item-value="id"
              item-title="name"
              :error-messages="createWizard.errors?.provider || []"
            />
            <s-text-field
              v-model="createWizard.form.identifier"
              label="Identifier"
              :error-messages="createWizard.errors?.identifier || []"
              spellcheck="false"
              class="mt-4"
            />
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <s-btn
              @click="createIdentity"
              :loading="createWizard.actionInProgress"
              color="primary"
              text="Save"
            />
          </v-card-actions>
        </template>
      </s-dialog>
    </v-card-text>
  </s-card>
</template>

<script setup lang="ts">
const route = useRoute();
const auth = useAuth();
const apiSettings = useApiSettings();

const user = await useFetchE<User>(`/api/v1/pentestusers/${route.params.userId}/`, { method: 'GET' });
const identities = await useFetchE<AuthIdentity[]>(`/api/v1/pentestusers/${route.params.userId}/identities/`, { method: 'GET' });

const createWizard = ref({
  visible: false,
  actionInProgress: false,
  errors: null as any|null,
  form: {
    provider: apiSettings.ssoAuthProviders[0]?.id,
    identifier: '',
  },
});
const canEdit = computed(() => auth.hasScope('user_manager') && !user.value.is_system_user);

async function createIdentity() {
  try {
    createWizard.value.actionInProgress = true;
    const obj = await $fetch<AuthIdentity>(`/api/v1/pentestusers/${user.value.id}/identities/`, {
      method: 'POST',
      body: createWizard.value.form
    });
    identities.value.push(obj);
    createWizard.value.visible = false;
  } catch (error: any) {
    if (error?.data) {
      createWizard.value.errors = error.data;
    }
    requestErrorToast({ error });
  } finally {
    createWizard.value.actionInProgress = false;
  }
}

async function deleteIdentity(identity: AuthIdentity) {
  await $fetch(`/api/v1/pentestusers/${user.value.id}/identities/${identity.id}/`, {
    method: 'DELETE'
  });
  identities.value = identities.value.filter(i => i.id !== identity.id);
}
</script>
