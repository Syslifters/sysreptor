<template>
  <v-container fluid class="fill-height">
    <v-row justify="center">
      <v-col xs="12" sm="8" md="4" align-self="center">
        <s-card>
          <v-toolbar theme="dark" class="login-header" flat>
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
            <s-btn
              to="/login/?logout=true"
              text="Back"
              color="primary"
            />
          </v-card-actions>
        </s-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { LoginResponse, LoginResponseStatus } from "~/utils/types";

definePageMeta({
  auth: false,
  title: 'Login',
});

const route = useRoute();
const auth = useAuth();
const { error } = useAsyncData(async () => {
  try {
    const res = await $fetch<LoginResponse>(`/api/v1/auth/login/`, {
      method: 'POST',
      body: route.query,
    });
    if (res.status === LoginResponseStatus.MFA_REQUIRED) {
      throw new Error('MFA required, but not supported for autologin');
    }
    await auth.fetchUser();
    await auth.redirect();
  } catch (error: any) {
    if (error?.data?.detail) {
      throw new Error(error.data.detail);
    } else if (error?.messages) {
      throw error;
    } else {
      throw new Error('Login failed');
    }
  }
});
</script>
