<template>
  <s-card>
    <v-toolbar dark class="login-header" flat tile>
      <v-toolbar-title><slot name="title">Login</slot></v-toolbar-title>
    </v-toolbar>

    <v-card-text>
      <v-list>
        <v-form v-for="authProvider in authProviders" :key="authProvider.id" @submit.prevent="authProviderLoginBegin(authProvider)">
          <v-list-item>
            <s-btn :key="authProvider.id" type="submit" color="primary" block>
              Login with {{ authProvider.name }}
            </s-btn>
          </v-list-item>
        </v-form>
        <slot name="append" />
      </v-list>
    </v-card-text>
  </s-card>
</template>

<script>
import { absoluteApiUrl } from '~/utils/urls';

export default {
  auth: false,
  computed: {
    authProviders() {
      return this.$store.getters['apisettings/settings'].auth_providers;
    }
  },
  mounted() {
    if (this.authProviders.length === 0) {
      this.$router.replace('/login/local/');
    }
  },
  methods: {
    authProviderLoginBegin(authProvider, options = { reauth: false }) {
      const url = new URL(absoluteApiUrl(`/auth/login/oidc/${authProvider.id}/begin/`, this.$axios), window.location);
      if (options.reauth) {
        url.searchParams.append('reauth', 'true');
      }
      window.location.assign(url.href);
    }
  }
}
</script>
