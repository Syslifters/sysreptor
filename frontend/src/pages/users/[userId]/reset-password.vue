<template>
  <v-form ref="form">
    <edit-toolbar :form="$refs.form" :save="changePassword" save-button-text="Reset Password">
      <template #title>Reset password of {{ user.username }}<template v-if="user.name"> ({{ user.name }})</template></template>
    </edit-toolbar>

    <s-password-field
      v-model="password"
      label="New password"
      :error-messages="serverErrors?.password || []"
      confirm show-strength
      :disabled="!canEdit"
    />
  </v-form>
</template>

<script setup lang="ts">
const route = useRoute();
const auth = useAuth();

const user = await useFetchE<User>(`/api/v1/pentestusers/${route.params.userId}/`, { method: 'GET' });

const password = ref(null);
const serverErrors = ref<any|null>(null);

const canEdit = computed(() => auth.hasScope('user_manager') && !user.value!.is_system_user);

async function changePassword() {
  try {
    await $fetch(`/api/v1/pentestusers/${user.value!.id}/reset-password/`, {
      method: 'POST',
      body: {
        password: password.value
      }
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
