<template>
  <v-container fluid fill-height>
    <v-layout align-center justify-center>
      <v-flex xs12 sm8 md4>
        <login-form v-if="step === 'local'" :username="$auth.user.username" @login="onLogin">
          <template #title>Re-Authenticate</template>
          <template #actions>
            <s-btn v-if="authProviders.length > 1" @click="step = 'list'" color="secondary">
              Back
            </s-btn>
          </template>
        </login-form>
        <login-provider-form v-else ref="loginProviderForm">
          <template #title>Re-Authenticate</template>
          <template #local>
            <v-list-item>
              <s-btn @click="step = 'local'" color="secondary" block>
                Login with local user
              </s-btn>
            </v-list-item>
          </template>
        </login-provider-form>
      </v-flex>
    </v-layout>
  </v-container>
</template>

<script>
import { authProviderLoginBegin } from '~/components/LoginProviderForm';

export default {
  async asyncData(context) {
    const authProviders = context.store.getters['apisettings/settings'].auth_providers;
    let defaultReauthProvider = authProviders.find(p => p.id === context.store.getters['apisettings/settings'].default_reauth_provider);
    if (!defaultReauthProvider && authProviders.length === 1) {
      defaultReauthProvider = authProviders[0];
    }
    if (!defaultReauthProvider && context.$auth.user.can_login_local) {
      defaultReauthProvider = authProviders.find(p => p.type === 'local');
    }

    let step = 'list';
    if (defaultReauthProvider?.type === 'local') {
      // Use the login form
      step = 'local';
    } else if (defaultReauthProvider) {
      await authProviderLoginBegin(defaultReauthProvider, context, { reauth: true });
    }

    return { step };
  },
  head: {
    title: 'Re-Authenticate',
  },
  computed: {
    authProviders() {
      return this.$store.getters['apisettings/settings'].auth_providers;
    },
    ssoEnabled() {
      return this.authProviders.some(p => ['oidc', 'remoteuser'].includes(p.type));
    },
  },
  methods: {
    onLogin() {
      this.$auth.redirect('home');
    },
  }
}
</script>
