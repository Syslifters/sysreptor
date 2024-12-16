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
    />

    <s-checkbox
      v-model="form.must_change_password"
      hint="The user has to change the password at the next login."
      :error-message="serverErrors?.must_change_password || []"
      :disabled="!canEdit || !apiSettings.isProfessionalLicense"
    >
      <template #label><pro-info>Must change password</pro-info></template>
    </s-checkbox>

    <s-btn-secondary
      type="submit"
      :disabled="!canEdit"
      class="mt-4"
    >
      Change password
    </s-btn-secondary>
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
</script>
