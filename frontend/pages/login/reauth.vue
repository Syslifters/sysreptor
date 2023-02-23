<template>
  <v-container fluid fill-height>
    <v-layout align-center justify-center>
      <v-flex xs12 sm8 md4>
        <login-form v-if="$auth.user.can_login_local" :username="$auth.user.username" @login="onLogin">
          <template #title>Re-Authenticate</template>
        </login-form>
        <login-oidc-form v-else ref="loginOidcForm">
          <template #title>Re-Authenticate</template>
        </login-oidc-form>
        <v-container fluid fill-height>
          <v-layout align-center justify-center>
            <v-flex xs12 sm8 md4>
            </v-flex>
          </v-layout>
        </v-container>
      </v-flex>
    </v-layout>
  </v-container>
</template>

<script>
export default {
  head: {
    title: 'Re-Authenticate',
  },
  mounted() {
    const authProviders = this.$store.getters['apisettings/settings'].auth_providers;
    if (!this.$auth.user.can_login_local && this.$auth.user.can_login_oidc && authProviders.length === 1) {
      this.$refs.loginOidcForm.authProviderLoginBegin(authProviders[0], { reauth: true });
    }
  },
  methods: {
    onLogin() {
      this.$auth.redirect('home');
    },
  }
}
</script>
