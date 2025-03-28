<template>
  <v-container fluid class="fill-height">
    <v-row justify="center">
      <v-col xs="12" sm="8" md="4" align-self="center">
        <s-card>
          <v-toolbar
            title="Forgot Password?"
            color="header" 
            flat
          />
          <v-form ref="form" @submit.prevent="resetPassword">
            <v-card-text>
              <v-text-field
                v-model="formResetPassword.email"
                type="email"
                name="email"
                label="E-mail"
                :error-messages="errorMessage"
                prepend-icon="mdi-email"
                variant="outlined"
                spellcheck="false"
                autocomplete="off"
                required
              />
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <s-btn-other
                to="/login/local/"
                text="Cancel"
              />
              <s-btn-primary
                type="submit"
                text="Reset Password"
                :loading="actionInProgress"
              />
            </v-card-actions>
          </v-form>
        </s-card>
      </v-col>

      <v-dialog v-model="resetPasswordSuccess" contained max-width="50%">
        <v-card rounded="lg">
          <template #text>
            <div class="text-center pt-4">
              <v-avatar
                class="mb-4"
                color="success"
                icon="mdi-check"
                size="x-large"
                variant="tonal"
              />

              <div class="font-weight-bold mb-1">
                Password reset mail sent
              </div>

              <div class="text-body-2 text-medium-emphasis mb-6">
                If your email address is associated with a user, you will now receive an email to reset your password. 
              </div>

              <s-btn-primary
                to="/login/local/"
                text="Proceed to login"
              />
            </div>
          </template>
        </v-card>
      </v-dialog>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
definePageMeta({
  auth: false,
  title: 'Forgot Password',
});

const actionInProgress = ref(false);
const errorMessage = ref<string | null>(null);
const formResetPassword = ref({ email: '', })
const resetPasswordSuccess = ref(false);

async function resetPassword() {
  if (actionInProgress.value) {
    return;
  }
  try {
    actionInProgress.value = true;
    errorMessage.value = null;

    await $fetch('/api/v1/auth/forgot-password/', { 
      method: 'POST', 
      body: formResetPassword.value 
    });
    resetPasswordSuccess.value = true;
  } catch (error: any) {
    if (error?.data?.detail) {
      errorMessage.value = error.data.detail;
    } else if (error?.data?.email) {
      errorMessage.value = error.data.email;
    }
    requestErrorToast({ error, message: 'Failed to send password reset email' });
  } finally {
    actionInProgress.value = false;
  }
}
</script>
