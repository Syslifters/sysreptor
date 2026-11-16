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
              <v-chip
                v-if="apiToken.permissions != null"
                size="small"
                class="ml-3"
              >
                Restricted permissions
              </v-chip>
              <template v-if="apiToken.projects != null">
                <v-chip v-for="project in apiToken.projects" :key="project.id" size="small" class="ml-1">
                  {{ project.name }}
                </v-chip>
                <v-chip v-if="apiToken.projects.length === 0" size="small" class="ml-1">No projects available</v-chip>
              </template>
              <v-chip
                v-if="apiToken.admin_permissions_enabled"
                size="small"
                class="ml-3"
              >
                Admin
              </v-chip>
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
              <template #title>Create API Token</template>
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
                      class="mb-4"
                    >
                      <template #label><pro-info>Expire Date (optional)</pro-info></template>
                    </s-date-picker>

                    <s-select
                      v-model="permissionLevel"
                      :items="permissionLevelItems"
                      item-props
                      :hint="permissionLevelItems.find(i => i.value === permissionLevel)?.subtitle"
                      persistent-hint
                      :error-messages="setupWizard.errors?.admin_permissions_enabled"
                      class="mb-4"
                    >
                      <template #label><pro-info>Permissions</pro-info></template>
                    </s-select>
                    <div v-if="permissionLevel === PermissionLevel.RESTRICTED" class="mb-2">
                      <s-autocomplete
                        v-model="customPermissions"
                        :items="availablePermissions"
                        label="Allowed permissions"
                        hint="Select at least one permission"
                        persistent-hint
                        multiple
                        chips
                        closable-chips
                        :error-messages="setupWizard.errors?.permissions"
                        class="mb-4"
                      />
                      <s-project-selection
                        v-model="selectedProjects"
                        label="Restrict to projects (optional)"
                        :query-filters="{ member: auth.user.value!.username }"
                        :error-messages="setupWizard.errors?.projects"
                        hint="Leave empty for all projects you can access. Requires project.read permission."
                      />
                    </div>

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
import { addMonths, formatISO9075 } from 'date-fns';

const route = useRoute();
const auth = useAuth();
const apiSettings = useApiSettings();

const apiTokens = await useAsyncDataE<ApiToken[]>(async () => {
  try {
    return await $fetch<ApiToken[]>('/api/v1/pentestusers/self/apitokens/', { method: 'GET' });
  } catch (error: any) {
    if (error?.data?.code === 'reauth-required') {
      auth.redirectToReAuth({ authRedirect: route.fullPath, replace: true });
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

enum PermissionLevel {
  ADMIN = 'admin',
  USER = 'user',
  RESTRICTED = 'restricted',
}

const reauthDialogVisible = ref(false);
const permissionLevel = ref<PermissionLevel>(PermissionLevel.USER);
const selectedProjects = ref<{ id: string; name: string }[]>([]);
const customPermissions = ref<string[]>([]);

const availablePermissions = computed(() => {
  // Use user's role permissions only.
  // user.effective_permissions would include all permissions for admins 
  // which cannot be used for restricted tokens.
  const roleIds = new Set(auth.user.value?.roles || []);
  const permissions = (apiSettings.settings?.permissions.roles || [])
    .filter(role => roleIds.has(role.id))
    .flatMap(role => role.permissions);
  return [...new Set(permissions)].sort();
});

const permissionLevelItems = computed(() => {
  const isPro = apiSettings.isProfessionalLicense;
  const items: { value: PermissionLevel; title: string; subtitle: string; disabled: boolean }[] = [];
  if (auth.permissions.value.superuser) {
    const adminEnabled = auth.permissions.value.admin;
    items.push({
      value: PermissionLevel.ADMIN,
      title: 'Admin permissions',
      subtitle: adminEnabled
        ? 'Token has full admin permissions.'
        : 'Enable admin permissions in your session to create an admin token.',
      disabled: !adminEnabled,
    });
  }
  items.push(
    {
      value: PermissionLevel.USER,
      title: 'User permissions',
      subtitle: 'Token uses your current permissions and project memberships.',
      disabled: !isPro,
    },
    {
      value: PermissionLevel.RESTRICTED,
      title: 'Restricted permissions',
      subtitle: 'Limit this token to selected permissions and optionally projects.',
      disabled: !isPro,
    },
  );
  return items;
});

const setupWizard = ref({
  visible: false,
  step: SetupWizardStep.INFO,
  errors: null as any|null,
  actionInProgress: false,
  newApiToken: null as ApiToken|null,
  form: {
    name: '',
    expire_date: null as string|null,
  },
});

function openSetupWizard() {
  permissionLevel.value = apiSettings.isProfessionalLicense ? PermissionLevel.USER : PermissionLevel.ADMIN;
  selectedProjects.value = [];
  customPermissions.value = [];
  setupWizard.value = {
    visible: true,
    step: SetupWizardStep.INFO,
    errors: null,
    actionInProgress: false,
    newApiToken: null,
    form: {
      name: 'API Token',
      expire_date: apiSettings.isProfessionalLicense ? formatISO9075(addMonths(new Date(), 3), { representation: 'date' }) : null,
    }
  };
}

async function createApiToken() {
  if (setupWizard.value.actionInProgress) {
    return;
  }
  if (permissionLevel.value === PermissionLevel.RESTRICTED && customPermissions.value.length === 0) {
    setupWizard.value.errors = { permissions: ['Select at least one permission.'] };
    return;
  }
  setupWizard.value.actionInProgress = true;
  try {
    const isRestricted = permissionLevel.value === PermissionLevel.RESTRICTED;
    setupWizard.value.newApiToken = await $fetch<ApiToken>('/api/v1/pentestusers/self/apitokens/', {
      method: 'POST',
      body: {
        ...setupWizard.value.form,
        permissions: isRestricted ? customPermissions.value : null,
        projects: isRestricted && selectedProjects.value.length > 0
          ? selectedProjects.value.map(p => ({ id: p.id }))
          : null,
        admin_permissions_enabled: permissionLevel.value === PermissionLevel.ADMIN,
      },
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
  } finally {
    setupWizard.value.actionInProgress = false;
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
