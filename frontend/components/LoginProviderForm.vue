<template>
  <s-card>
    <v-toolbar dark class="login-header" flat tile>
      <v-toolbar-title><slot name="title">Login</slot></v-toolbar-title>
    </v-toolbar>

    <v-card-text>
      <v-list>
        <v-form v-for="oidcProvider in oidcProviders" :key="oidcProvider.id" @submit.prevent="authProviderLoginBegin(oidcProvider)">
          <v-list-item>
            <s-btn :key="oidcProvider.id" type="submit" color="primary" block>
              Login with {{ oidcProvider.name }}
            </s-btn>
          </v-list-item>
        </v-form>

        <slot v-if="remoteUserAuthProvider" name="remote">
          <v-list-item>
            <s-btn @click="authProviderLoginBegin(remoteUserAuthProvider)" nuxt color="primary" block>
              Login with {{ remoteUserAuthProvider.name }}
            </s-btn>
          </v-list-item>
        </slot>
        
        <slot v-if="localUserAuthEnabled" name="local">
          <v-list-item>
            <s-btn to="/login/local" nuxt color="secondary" block>
              Login with local user
            </s-btn>
          </v-list-item>
        </slot>
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
    },
    oidcProviders() {
      return this.authProviders.filter(p => p.type === 'oidc');
    },
    localUserAuthEnabled() {
      return this.authProviders.some(p => p.type === 'local');
    },
    remoteUserAuthProvider() {
      return this.authProviders.find(p => p.type === 'remoteuser');
    }
  },
  methods: {
    async authProviderLoginBegin(authProvider, options = { reauth: false }) {
      return await authProviderLoginBegin(authProvider, this.$nuxt.context, options);
    }
  }
}

export async function authProviderLoginBegin(authProvider, { redirect, $axios, $auth, $toast }, options = { reauth: false }) {
  if (authProvider.type === 'local') {
    redirect('/login/local/');
  } else if (authProvider.type === 'remoteuser') {
    try {
      await $axios.$post('/auth/login/remoteuser/', {});
      await $auth.fetchUser();
      $auth.redirect('home');
    } catch (error) {
      $toast.global.requestError({ error, message: 'Login failed' });
    }
  } else if (authProvider.type === 'oidc') {
    const url = new URL(absoluteApiUrl(`/auth/login/oidc/${authProvider.id}/begin/`, $axios), window.location);
    if (options.reauth) {
      url.searchParams.append('reauth', 'true');
    }
    try {
      redirect(url.href);
    } catch (error) {
      // ignore error: redirect outside of vue 
    }
  }
}
</script>
