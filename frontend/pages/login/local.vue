<template>
  <v-container fluid fill-height>
    <v-layout align-center justify-center>
      <v-flex xs12 sm8 md4>
        <login-form @login="onLogin">
          <template #message>
            <p v-if="licenseErrorMessage" class="red--text">
              <v-icon color="red" class="mr-1">mdi-alert-decagram</v-icon>
              Software License Error: {{ licenseErrorMessage }}.<br>
              Falling back to a free Community license. Some features are disabled.<br>
              See <a href="https://docs.sysreptor.com/features-and-pricing/" target="_blank">https://docs.sysreptor.com/features-and-pricing/</a>
            </p>
          </template>

          <template #actions>
            <s-btn v-if="oidcEnabled" to="/login/" nuxt color="secondary">
              Back
            </s-btn>
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
              <s-btn @click="mfaSetupNotificationVisible = false" color="secondary">
                Skip
              </s-btn>
              <s-btn to="/users/self/security/" nuxt color="primary">
                Set up MFA
              </s-btn>
            </v-card-actions>
          </template>
        </s-dialog>
      </v-flex>
    </v-layout>
  </v-container>
</template>

<script>
export default {
  auth: false,
  data() {
    return {
      mfaSetupNotificationVisible: false,
    };
  },
  head: {
    title: 'Login',
  },
  computed: {
    oidcEnabled() {
      return this.$store.getters['apisettings/settings'].auth_providers.length > 0;
    },
    licenseErrorMessage() {
      return this.$store.getters['apisettings/settings'].license.error;
    },
  },
  watch: {
    mfaSetupNotificationVisible(newValue, oldValue) {
      // on dialog closed
      if (!newValue && oldValue) {
        this.completeLogin();
      } 
    }
  },
  methods: {
    onLogin(res) {
      if (!this.$auth.user.is_mfa_enabled && (this.$auth.user.is_superuser || res.first_login)) {
        this.mfaSetupNotificationVisible = true;
      } else {
        this.completeLogin();
      }
    },
    completeLogin() {
      this.$auth.redirect('home');
    }
  }
}
</script>
