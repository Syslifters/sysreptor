<template>
  <v-container fluid class="fill-height">
    <v-row justify="center">
      <v-col xs="12" sm="8" md="4" align-self="center">
        <s-card>
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
              text="Back"
            />
          </v-card-actions>
        </s-card>
      </v-col>
    </v-row>
  </v-container>
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
    await $fetch(`/api/v1/auth/login/oidc/${route.params.authProviderId}/complete/`, {
      method: 'GET',
      params: route.query,
    });
    await auth.fetchUser();
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
