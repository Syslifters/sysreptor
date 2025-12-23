<template>
  <v-container fluid class="fill-height">
    <v-row justify="center">
      <v-col xs="12" sm="8" md="4" align-self="center">
        <login-form @login="onLogin">
          <template #message>
            <div v-if="apiSettings.settings!.features.forgot_password" class="text-end">
              <v-btn 
                to="/login/forgot-password/"
                text="Forgot password?"
                variant="plain"
                density="compact"
                class="text-none"
              />
            </div>

            <p v-if="apiSettings.settings!.license.error" class="text-error">
              <v-icon start color="error" icon="mdi-alert-decagram" />
              Software License Error: {{ apiSettings.settings!.license.error }}.<br>
              Falling back to a free Community license. Some features are disabled.<br>
              See <a href="https://sysreptor.com/pricing" target="_blank">https://sysreptor.com/pricing</a>
            </p>
          </template>

          <template #actions>
            <s-btn-other
              v-if="auth.loggedIn.value"
              to="/"
              text="Cancel"
            />
            <s-btn-secondary
              v-if="apiSettings.isSsoEnabled"
              to="/login/?logout=true"
              text="Use another method"
            />
          </template>
        </login-form>

        <s-dialog v-model="mfaSetupNotificationVisible">
          <template #title>Multi Factor Authentication</template>
          <template #default>
            <v-card-text>
              You do not have Multi Factor Authentication enabled for your account. <br>
              We recommend to set up MFA to increase your account security.
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <s-btn-other
                data-testid="mfa-setup-skip"
                text="Skip"
                @click="auth.redirect()"
              />
              <s-btn-primary
                text="Set up MFA"
                to="/users/self/security/"
              />
            </v-card-actions>
          </template>
        </s-dialog>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
definePageMeta({
  auth: false,
  title: 'Login',
})

const auth = useAuth();
const apiSettings = useApiSettings();
const mfaSetupNotificationVisible = ref(false);

function onLogin(res: LoginResponse) {
  if (!auth.user.value!.is_mfa_enabled && (auth.user.value!.is_superuser || res.first_login)) {
    mfaSetupNotificationVisible.value = true;
  } else {
    auth.redirect();
  }
}
</script>
