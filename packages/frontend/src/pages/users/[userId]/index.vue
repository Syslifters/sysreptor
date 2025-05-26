<template>
  <v-form ref="form">
    <edit-toolbar
      :data="user"
      :form="form"
      :edit-mode="canEdit ? EditMode.EDIT : EditMode.READONLY"
      :save="performSave"
      :delete="performDelete"
      :delete-confirm-input="user.username || undefined"
    />

    <user-info-form v-model="user" :errors="serverErrors" :can-edit-permissions="canEdit" :can-edit-username="canEdit">
      <template #login-information>
        <div class="mt-4 mb-4">
          <s-btn-secondary
            v-if="canEdit"
            :to="`/users/${user.id}/reset-password/`"
            text="Reset Password"
            class="mr-2"
          />
          <btn-confirm
            v-if="apiSettings.settings!.features.forgot_password"
            :action="performSendPasswordResetEmail"
            :confirm="false"
            button-text="Send password reset email"
            :disabled="!user.email || !user.is_active"
          />
        </div>

        <v-row>
          <v-col>
            <s-checkbox
              v-model="user.is_active"
              :disabled="!canEdit || user.id === auth.user.value!.id"
              label="User is active"
              hint="Inactive users cannot log in"
              density="compact"
            />
          </v-col>
          <v-col>
            <s-checkbox
              v-model="user.must_change_password"
              :disabled="!canEdit || !apiSettings.isProfessionalLicense || !canLoginLocal"
              hint="The user has to change the password at the next login."
              density="compact"
            >
              <template #label><pro-info>Must change password</pro-info></template>
            </s-checkbox>
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <s-checkbox
              :model-value="apiSettings.isLocalUserAuthEnabled ? user.can_login_local : false"
              @update:model-value="user.can_login_local = $event"
              :disabled="!canEdit || !apiSettings.isLocalUserAuthEnabled || !apiSettings.isProfessionalLicense"
              label="Can login via username/password"
              hint="The user can log in with username and password. Disable to force SSO login for this user."
              density="compact"
            />
          </v-col>
          <v-col>
            <s-checkbox
              v-model="user.can_login_sso"
              :disabled="true"
              hint="The user can login with an authentication provider. Linked identities are configured."
              density="compact"
            >
              <template #label><pro-info>Can login via SSO</pro-info></template>
            </s-checkbox>
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <s-checkbox
              v-if="apiSettings.isLocalUserAuthEnabled && !user.is_system_user"
              v-model="user.is_mfa_enabled"
              label="Is Multi Factor Authentication enabled"
              disabled
              density="compact"
            />
          </v-col>
        </v-row>

        <p v-if="!user.is_system_user" class="mt-4">
          Last login: <chip-date :value="user.last_login" />
        </p>
      </template>
    </user-info-form>
  </v-form>
</template>

<script setup lang="ts">
import { VForm } from "vuetify/components";
import { EditMode } from "#imports";

const route = useRoute();
const auth = useAuth();
const apiSettings = useApiSettings();

const apiUrl = `/api/v1/pentestusers/${route.params.userId}/`
const user = await useAsyncDataE<User>(async () => await $fetch(apiUrl, { method: 'GET' }), { deep: true });

const serverErrors = ref<any|null>(null);
const canEdit = computed(() => auth.permissions.value.user_manager && !user.value.is_system_user);
const canLoginLocal = computed(() => user.value.can_login_local && apiSettings.isLocalUserAuthEnabled);

const form = useTemplateRef('form');

async function performSave(data: User) {
  try {
    await $fetch(apiUrl, {
      method: 'PATCH',
      body: data
    });
    serverErrors.value = null;
  } catch (error: any) {
    if (error?.status === 400 && error?.data) {
      serverErrors.value = error.data;
    }
    throw error;
  }
}

async function performDelete() {
  await $fetch(apiUrl, { method: 'DELETE' });
  successToast('User deleted');
  await navigateTo('/users/');
}

async function performSendPasswordResetEmail() {
  await $fetch(`/api/v1/auth/forgot-password/`, {
    method: 'POST',
    body: {
      email: user.value.email,
    },
  });
  successToast('Password reset email sent. The user has to click the link in the email to reset the password.');
}
</script>
