<template>
  <v-container fluid fill-height>
    <v-layout align-center justify-center>
      <v-flex xs12 sm8 md4>
        <login-provider-form />
      </v-flex>
    </v-layout>
  </v-container>
</template>

<script>
import { authProviderLoginBegin } from '~/components/LoginProviderForm';

export default {
  auth: false,
  async asyncData(context) {
    // Do not auto-login after logout
    if (!context.route.query?.logout) {
      const authProviders = context.store.getters['apisettings/settings'].auth_providers;
      let defaultAuthProvider = authProviders.find(p => p.id === context.store.getters['apisettings/settings'].default_auth_provider);
      if (!defaultAuthProvider && authProviders.length === 1) {
        defaultAuthProvider = authProviders[0];
      }  
      if (defaultAuthProvider) {
        await authProviderLoginBegin(defaultAuthProvider, context);
      }
    }
    return {};
  },
  head: {
    title: 'Login',
  },
  computed: {
    localUserAuthEnabled() {
      return this.$store.getters['apisettings/settings'].auth_providers.some(p => p.type === 'local');
    },
  },
}
</script>
