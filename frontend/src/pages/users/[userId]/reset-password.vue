<template>
  <v-form ref="form" @submit.prevent="changePassword">
    <v-toolbar density="compact" flat color="inherit">
      <v-toolbar-title>
        Reset password of {{ user.username }}<template v-if="user.name"> ({{ user.name }})</template>
      </v-toolbar-title>
    </v-toolbar>

    <s-password-field
      v-model="password"
      label="New password"
      :error-messages="serverErrors?.password || []"
      confirm show-strength
      :disabled="!canEdit"
    />

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

const user = await useFetchE<User>(`/api/v1/pentestusers/${route.params.userId}/`, { method: 'GET' });

const password = ref(null);
const serverErrors = ref<any|null>(null);

const canEdit = computed(() => auth.hasScope('user_manager') && !user.value!.is_system_user);

const form = ref<VForm>();
async function changePassword() {
  if (!((await form.value!.validate()).valid)) {
    return;
  }

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
