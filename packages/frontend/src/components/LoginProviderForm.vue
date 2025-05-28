<template>
  <s-card>
    <v-toolbar color="header" flat>
      <v-toolbar-title><slot name="title">Login</slot></v-toolbar-title>
    </v-toolbar>

    <v-card-text>
      <v-list>
        <v-form v-for="oidcProvider in oidcAuthProviders" :key="oidcProvider.id" @submit.prevent="auth.authProviderLoginBegin(oidcProvider, { reauth: props.reauth })">
          <v-list-item>
            <s-btn-primary :key="oidcProvider.id" type="submit" block>
              Login with {{ oidcProvider.name }}
            </s-btn-primary>
          </v-list-item>
        </v-form>

        <slot v-if="remoteUserAuthProvider" name="remote">
          <v-list-item>
            <s-btn-primary @click="auth.authProviderLoginBegin(remoteUserAuthProvider, { reauth: props.reauth })" block>
              Login with {{ remoteUserAuthProvider.name }}
            </s-btn-primary>
          </v-list-item>
        </slot>

        <slot v-if="isLocalUserAuthEnabled" name="local">
          <v-list-item>
            <s-btn-secondary to="/login/local" block>
              Login with local user
            </s-btn-secondary>
          </v-list-item>
        </slot>
      </v-list>
    </v-card-text>
    <v-card-actions v-if="$slots.actions">
      <v-spacer />
      <slot name="actions" />
    </v-card-actions>
  </s-card>
</template>

<script setup lang="ts">
const apiSettings = useApiSettings();
const auth = useAuth();

const props = defineProps<{
  authProviders?: AuthProvider[];
  reauth?: boolean;
}>();

const authProviders = computed(() => props.authProviders || apiSettings.settings?.auth_providers || []);
const oidcAuthProviders = computed(() => authProviders.value.filter(p => p.type === AuthProviderType.OIDC));
const remoteUserAuthProvider = computed(() => authProviders.value.find(p => p.type === AuthProviderType.REMOTEUSER));
const isLocalUserAuthEnabled = computed(() => authProviders.value.some(p => p.type === AuthProviderType.LOCAL));
</script>
