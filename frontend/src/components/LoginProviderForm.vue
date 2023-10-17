<template>
  <s-card>
    <v-toolbar theme="dark" class="login-header" flat>
      <v-toolbar-title><slot name="title">Login</slot></v-toolbar-title>
    </v-toolbar>

    <v-card-text>
      <v-list>
        <v-form v-for="oidcProvider in apiSettings.oidcAuthProviders" :key="oidcProvider.id" @submit.prevent="auth.authProviderLoginBegin(oidcProvider)">
          <v-list-item>
            <s-btn :key="oidcProvider.id" type="submit" color="primary" block>
              Login with {{ oidcProvider.name }}
            </s-btn>
          </v-list-item>
        </v-form>

        <slot v-if="apiSettings.remoteUserAuthProvider" name="remote">
          <v-list-item>
            <s-btn @click="auth.authProviderLoginBegin(apiSettings.remoteUserAuthProvider)" color="primary" block>
              Login with {{ apiSettings.remoteUserAuthProvider.name }}
            </s-btn>
          </v-list-item>
        </slot>

        <slot v-if="apiSettings.isLocalUserAuthEnabled" name="local">
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

<script setup lang="ts">
const apiSettings = useApiSettings();
const auth = useAuth();
</script>
