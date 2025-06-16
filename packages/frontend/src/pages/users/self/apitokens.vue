<template>
  <div>
    <s-dialog v-model="reauthDialogVisible">
      <template #title>Re-Authentication required</template>
      <template #default>
        <v-card-text>
          This operation requires a re-authentication.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <s-btn-other
            @click="reauthDialogVisible = false"
            text="Cancel"
          />
          <s-btn-primary
            @click="auth.redirectToReAuth()"
            text="Re-Authenticate"
          />
        </v-card-actions>
      </template>
    </s-dialog>

    <s-card class="mt-4">
      <v-card-title>API Tokens</v-card-title>
      <v-card-text>
        <p>
          Use the <a href="https://docs.sysreptor.com/cli/getting-started/" target="_blank" class="text-primary">reptor CLI</a>, 
          or the <a href="/api/public/utils/swagger-ui/" target="_blank" class="text-primary">SysReptor REST API</a> (unstable).
        </p>
        <pre class="token-preview mt-2"><s-code>Authorization: Bearer &lt;api_token&gt;</s-code></pre>

        <v-list>
          <v-list-item
            v-for="apiToken in apiTokens" :key="apiToken.id"
            prepend-icon="mdi-key-variant"
          >
            <v-list-item-title>
              {{ apiToken.name }}
              <chip-expires class="ml-3" :value="apiToken.expire_date" />
              <chip-date :value="apiToken.last_used" label="Last Used" />
              <chip-created :value="apiToken.created" />
            </v-list-item-title>
            <template #append>
              <btn-delete button-variant="icon" :delete="() => deleteApiToken(apiToken)" />
            </template>
          </v-list-item>
          <v-list-item>
            <s-dialog v-model="setupWizard.visible">
              <template #activator="{ props: dialogProps}">
                <s-btn-secondary
                  @click="openSetupWizard"
                  v-bind="dialogProps"
                  prepend-icon="mdi-plus"
                  text="Add"
                />
              </template>
              <template #title>Setup API Token</template>
              <template #default>
                <template v-if="setupWizard.step === SetupWizardStep.INFO">
                  <v-card-text>
                    <s-text-field
                      v-model="setupWizard.form.name"
                      label="Name"
                      :error-messages="setupWizard.errors?.name"
                      class="mb-4"
                      autofocus
                      spellcheck="false"
                    />
                    <s-date-picker
                      v-model="setupWizard.form.expire_date"
                      label="Expire Date (optional)"
                      :error-messages="setupWizard.errors?.expire_date"
                      :min-date="formatISO9075(new Date(), { representation: 'date' })"
                      :disabled="!apiSettings.isProfessionalLicense"
                    >
                      <template #label><pro-info>Expire Date (optional)</pro-info></template>
                    </s-date-picker>

                    <v-alert v-if="setupWizard.errors?.detail" color="error" class="mt-4">
                      {{ setupWizard.errors.detail }}
                    </v-alert>
                  </v-card-text>
                  <v-card-actions>
                    <v-spacer />
                    <s-btn-other
                      @click="setupWizard.visible = false"
                      text="Cancel"
                    />
                    <s-btn-primary
                      @click="createApiToken"
                      :loading="setupWizard.actionInProgress"
                      text="Create"
                    />
                  </v-card-actions>
                </template>
                <template v-else-if="setupWizard.step === SetupWizardStep.TOKEN">
                  <v-card-text>
                    <p>
                      The API token <s-code>{{ setupWizard.newApiToken?.name }}</s-code> has been created successfully.<br>
                      Please copy the token and store it in a safe place.
                      You will not be able to see it again.
                    </p>
                    <s-code class="token-preview">
                      Authorization: Bearer {{ setupWizard.newApiToken?.token }}
                      <s-btn-icon 
                        @click="copyToClipboard(setupWizard.newApiToken?.token || '')" 
                        icon="mdi-content-copy" 
                        size="small"
                        density="compact"
                        class="ml-2"
                      />
                    </s-code>
                    
                  </v-card-text>
                  <v-card-actions>
                    <v-spacer />
                    <s-btn-primary
                      @click="setupWizard.visible = false"
                      text="Done"
                    />
                  </v-card-actions>
                </template>
              </template>
            </s-dialog>
          </v-list-item>
        </v-list>
      </v-card-text>
    </s-card>
  </div>
</template>

<script setup lang="ts">
import { formatISO9075 } from 'date-fns';

const auth = useAuth();
const apiSettings = useApiSettings();

const apiTokens = await useAsyncDataE<ApiToken[]>(async () => {
  try {
    return await $fetch<ApiToken[]>('/api/v1/pentestusers/self/apitokens/', { method: 'GET' });
  } catch (error: any) {
    if (error?.data?.code === 'reauth-required') {
      auth.redirectToReAuth({ replace: true });
      return [];
    } else {
      throw error;
    }
  }
});

enum SetupWizardStep {
  INFO = 'info',
  TOKEN = 'token',
}

const reauthDialogVisible = ref(false);
const setupWizard = ref({
  visible: false,
  step: SetupWizardStep.INFO,
  form: {
    name: '',
    expire_date: null as string|null,
  },
  errors: null as any|null,
  actionInProgress: false,
  newApiToken: null as ApiToken|null,
});

function openSetupWizard() {
  setupWizard.value = {
    visible: true,
    step: SetupWizardStep.INFO,
    form: {
      name: 'API Token',
      expire_date: null,
    },
    errors: null,
    actionInProgress: false,
    newApiToken: null
  };
}

async function createApiToken() {
  try {
    setupWizard.value.newApiToken = await $fetch<ApiToken>('/api/v1/pentestusers/self/apitokens/', {
      method: 'POST',
      body: setupWizard.value.form,
    });
    setupWizard.value.step = SetupWizardStep.TOKEN;
    apiTokens.value = [setupWizard.value.newApiToken].concat(apiTokens.value);
  } catch (error: any) {
    if (error?.data?.code === 'reauth-required') {
      setupWizard.value.visible = false;
      reauthDialogVisible.value = true;
    } else if (error?.data) {
      setupWizard.value.errors = error.data;
    } else {
      throw error;
    }
  }
}

async function deleteApiToken(apiToken: ApiToken) {
  try {
    await $fetch(`/api/v1/pentestusers/self/apitokens/${apiToken.id}/`, { method: 'DELETE' });
    apiTokens.value = apiTokens.value.filter(t => t.id !== apiToken.id);
  } catch (error) {
    requestErrorToast({ error });
  }
}
</script>

<style lang="scss" scoped>
.token-preview {
  white-space: pre-wrap;
  word-break: break-all;
  display: block;
}
</style>
