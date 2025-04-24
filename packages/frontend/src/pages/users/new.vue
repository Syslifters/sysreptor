<template>
  <v-container class="pt-0 h-100 overflow-y-auto">
    <v-form ref="form" @submit.prevent="performCreate">
      <edit-toolbar>
        <template #title>Create new User</template>
        <s-btn-primary 
          type="submit"
          text="Create"
          prepend-icon="mdi-content-save"
        />
      </edit-toolbar>

      <user-info-form v-model="userForm" :errors="serverErrors" :can-edit-permissions="true" :can-edit-username="true">
        <template #login-information>
          <div v-if="apiSettings.isLocalUserAuthEnabled">
            <s-password-field
              v-model="userForm.password"
              confirm show-strength generate
              :error-messages="serverErrors?.password || []"
              class="mt-4"
            />
            <s-checkbox
              v-model="userForm.must_change_password"
              label="Must change password"
              hint="The user has to change the password at the next login."
              :error-message="serverErrors?.must_change_password || []"
              :disabled="!apiSettings.isProfessionalLicense"
            >
              <template #label><pro-info>Must change password</pro-info></template>
            </s-checkbox>
          </div>
          <div v-if="apiSettings.isSsoEnabled" class="mt-4">
            SSO Authentication Identity (optional):
            <v-row>
              <v-col>
                <s-select
                  v-model="identityForm.provider"
                  label="Provider"
                  :items="apiSettings.ssoAuthProviders"
                  item-value="id"
                  item-title="name"
                />
              </v-col>
              <v-col>
                <s-text-field
                  v-model="identityForm.identifier"
                  label="Identifier"
                  spellcheck="false"
                />
              </v-col>
            </v-row>
          </div>
        </template>
      </user-info-form>
    </v-form>
  </v-container>
</template>
<script setup lang="ts">
import randomColor from 'randomcolor';
import type { VForm } from "vuetify/lib/components/index.mjs";

useHeadExtended({
  breadcrumbs: () => userListBreadcrumbs().concat([{ title: 'New', to: '/users/new/' }]),
});

const apiSettings = useApiSettings();

const userForm = ref<User & { password: string|null }>({
  username: null,
  password: null,
  title_before: null,
  first_name: '',
  middle_name: null,
  last_name: '',
  title_after: null,
  email: null,
  phone: null,
  mobile: null,
  color: randomColor({ luminosity: 'bright' }),
  must_change_password: apiSettings.isProfessionalLicense,
  is_superuser: !apiSettings.isProfessionalLicense,
  is_project_admin: false,
  is_user_manager: false,
  is_designer: false,
  is_template_editor: false,
  is_guest: false,
  is_system_user: false,
  is_global_archiver: false,
} as any);
const identityForm = ref({
  provider: null,
  identifier: null
});
const serverErrors = ref<any|null>();

const form = templateRef('form');
async function performCreate() {
  if (!(await form.value!.validate()).valid) {
    return;
  }

  try {
    const user = await $fetch<User>('/api/v1/pentestusers/', {
      method: 'POST',
      body: userForm.value,
    });

    if (identityForm.value.provider && identityForm.value.identifier) {
      try {
        await $fetch(`/api/v1/pentestusers/${user.id}/identities/`, {
          method: 'POST',
          body: identityForm.value,
        })
      } catch (error) {
        requestErrorToast({ error });
      }
    }
    await navigateTo(`/users/${user.id}/`)
  } catch (error: any) {
    if (error?.status === 400 && error?.data) {
      serverErrors.value = error.data;
    } else {
      requestErrorToast({ error });
    }
  }
}
</script>
