<template>
  <v-form ref="formRef" @submit.prevent="changePassword">
    <v-toolbar density="compact" flat color="inherit">
      <v-toolbar-title>
        Reset password of {{ user.username }}<template v-if="user.name"> ({{ user.name }})</template>
      </v-toolbar-title>
    </v-toolbar>

    <s-password-field
      v-model="form.password"
      label="New password"
      :error-messages="serverErrors?.password || []"
      confirm show-strength generate
      :disabled="!canEdit"
      class="mt-4"
    />

    <s-checkbox
      v-model="form.must_change_password"
      hint="The user has to change the password at the next login."
      :error-message="serverErrors?.must_change_password || []"
      :disabled="!canEdit || !apiSettings.isProfessionalLicense"
    >
      <template #label><pro-info>Must change password</pro-info></template>
    </s-checkbox>

    <div class="mt-4">
      <s-btn-primary
        type="submit"
        text="Change password"
        :disabled="!canEdit"
        class="mr-2"
      />
      <s-btn-secondary
        @click="sendPasswordResetEmail"
        type="button"
        text="Send password reset email"
        :disabled="!user.email || !user.is_active || !apiSettings.settings!.features.forgot_password"
      />
    </div>
  </v-form>
</template>

<script setup lang="ts">
import type { VForm } from 'vuetify/lib/components/index.mjs';

const route = useRoute();
const auth = useAuth();
const apiSettings = useApiSettings();

const user = await useFetchE<User>(`/api/v1/pentestusers/${route.params.userId}/`, { method: 'GET' });

const form = ref({
  password: '',
  must_change_password: apiSettings.isProfessionalLicense,
})
const serverErrors = ref<any|null>(null);

const canEdit = computed(() => auth.permissions.value.user_manager && !user.value!.is_system_user);

const formRef = ref<VForm>();
async function changePassword() {
  if (!((await formRef.value!.validate()).valid)) {
    return;
  }

  try {
    await $fetch(`/api/v1/pentestusers/${user.value!.id}/reset-password/`, {
      method: 'POST',
      body: form.value,
    });
    successToast('Password changed');
    await navigateTo(`/users/${user.value.id}/`);
  } catch (error: any) {
    if (error?.status === 400 && error?.data) {
      serverErrors.value = error.data;
    }
    throw error;
  }
}

async function sendPasswordResetEmail() {
  try {
    await $fetch(`/api/v1/auth/forgot-password/`, {
      method: 'POST',
      body: {
        email: user.value.email,
      },
    });
    successToast('Password reset email sent. The user has to click the link in the email to reset the password.');
    await navigateTo(`/users/${user.value.id}/`);
  } catch (error: any) {
    await requestErrorToast({ error, message: 'Failed to send password reset email' });
  }
}
</script>
