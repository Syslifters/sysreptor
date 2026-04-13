<template>
  <centered-view>
    <s-card class="w-100">
      <v-toolbar title="Set Password" color="header" flat />
      <v-form v-if="user" ref="form" @submit.prevent="performSetPassword">
        <v-card-text>
          <s-text-field
            v-model="user.username"
            type="text"
            name="username"
            label="Username"
            prepend-inner-icon="mdi-account"
            disabled
          />
          <s-password-field
            v-model="formSetPassword.password"
            :error-messages="formError?.data?.detail"
            confirm show-strength generate
            label="New Password"
            autocomplete="new-password"
            class="mt-4"
          />
          <v-alert v-if="formError?.data?.detail" type="error" :text="formError.data.detail" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <s-btn-primary
            type="submit"
            text="Submit"
          />
        </v-card-actions>
      </v-form>
      <v-card-text v-else-if="checkTokenError">
        <v-alert color="error">
          {{ checkTokenError?.message }}
        </v-alert>
      </v-card-text>
      <div v-else class="mt-4 d-flex flex-column align-center">
        <v-progress-circular indeterminate size="50" />
      </div>
    </s-card>
  </centered-view>
</template>

<script setup lang="ts">
import { VForm } from 'vuetify/components';

definePageMeta({
  auth: false,
  title: 'Login',
});

const route = useRoute();

const { data: user, error: checkTokenError } = useAsyncData(async () => {
  try {
    return await $fetch<UserShortInfo>('/api/v1/auth/forgot-password/check/', {
      method: 'POST',
      body: route.query,
    });
  } catch (error: any) {
    if (error.data.detail) {
      throw new Error(error.data.detail);
    } else {
      throw new Error('Failed to reset password');
    }
  }
});

const form = ref<InstanceType<typeof VForm>>();
const formSetPassword = ref({ password: '' });
const formError = ref<any|null>(null);
async function performSetPassword() {
  try {
    await $fetch('/api/v1/auth/forgot-password/reset/', {
      method: 'POST',
      body: {
        ...route.query,
        ...formSetPassword.value,
      },
    });
    successToast('Password changed');
    await navigateTo('/login/local/');
  } catch (error: any) {
    formError.value = error;
    requestErrorToast({ error })
  }
}

</script>
