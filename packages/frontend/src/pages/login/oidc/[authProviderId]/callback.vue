<template>
  <centered-view>
    <s-card class="w-100">
      <v-toolbar color="header" flat>
        <v-toolbar-title>Login</v-toolbar-title>
      </v-toolbar>

      <v-card-text v-if="error">
        <v-alert color="error">
          {{ error?.message }}
        </v-alert>
      </v-card-text>
      <div v-else class="mt-4 d-flex flex-column align-center">
        <v-progress-circular indeterminate size="50" />
      </div>

      <v-card-actions>
        <v-spacer />
        <s-btn-other
          v-if="auth.loggedIn.value"
          to="/"
          text="Cancel"
        />
        <s-btn-secondary
          to="/login/?logout=true"
          text="Use another method"
        />
      </v-card-actions>
    </s-card>
  </centered-view>
</template>

<script setup lang="ts">
definePageMeta({
  auth: false,
  title: 'Login',
});

const route = useRoute();
const auth = useAuth();
const { error } = useAsyncData(async () => {
  try {
    const res = await $fetch<LoginResponse>(`/api/v1/auth/login/oidc/${route.params.authProviderId}/complete/`, {
      method: 'GET',
      params: route.query,
    });
    await auth.finishLogin(res);
    await auth.redirect();
  } catch (error: any) {
    if (error?.data?.detail) {
      throw new Error(error.data.detail);
    } else {
      throw new Error('Login failed');
    }
  }
});
</script>
