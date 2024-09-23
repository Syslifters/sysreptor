<template>
  <v-form ref="form">
    <edit-toolbar
      :data="user"
      :form="$refs.form as VForm"
      :edit-mode="canEdit ? EditMode.EDIT : EditMode.READONLY"
      :save="performSave"
      :delete="performDelete"
      :delete-confirm-input="user.username || undefined"
    />

    <user-info-form v-model="user" :errors="serverErrors" :can-edit-permissions="canEdit" :can-edit-username="canEdit">
      <template #login-information>
        <s-btn-secondary
          v-if="canEdit"
          :to="`/users/${user.id}/reset-password/`"
          text="Reset Password"
          class="mt-4 mb-4"
        />

        <s-checkbox
          v-model="user.is_active"
          :disabled="!canEdit || user.id === auth.user.value!.id"
          label="User is active"
          hint="Inactive users cannot log in"
          density="compact"
        />
        <s-checkbox
          v-model="user.can_login_local"
          label="Local user"
          hint="The user can log in with username and password."
          disabled
          density="compact"
        />
        <s-checkbox
          v-if="apiSettings.isSsoEnabled"
          v-model="user.can_login_sso"
          label="SSO user"
          hint="The user can login with an authentication provider. Linked identities are configured."
          disabled
          density="compact"
        />
      </template>
      <s-checkbox
        v-if="apiSettings.isLocalUserAuthEnabled && !user.is_system_user"
        v-model="user.is_mfa_enabled"
        label="Is Multi Factor Authentication enabled"
        disabled
      />
      <p v-if="!user.is_system_user" class="mt-4">
        Last login: {{ user.last_login || 'Never' }}
      </p>
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
</script>
