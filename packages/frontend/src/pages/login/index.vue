<template>
  <centered-view>
    <login-provider-form class="w-100">
      <template #actions v-if="auth.loggedIn.value">
        <s-btn-other
          to="/"
          text="Cancel"
        />
      </template>
    </login-provider-form>
  </centered-view>
</template>

<script setup lang="ts">
definePageMeta({
  auth: false,
  title: 'Login',
});

const route = useRoute();
const auth = useAuth();
const apiSettings = useApiSettings();

useLazyAsyncData(async () => {
  const authProviders = apiSettings.settings!.auth_providers;
  let defaultAuthProvider = authProviders.find(p => p.id === apiSettings.settings!.default_auth_provider);
  if (!defaultAuthProvider && authProviders.length === 1) {
    defaultAuthProvider = authProviders[0];
  }

  if (defaultAuthProvider) {
    // Do not auto-login after logout
    if (!route.query?.logout || (authProviders.length === 1 && defaultAuthProvider.type === AuthProviderType.LOCAL)) {
      await auth.authProviderLoginBegin(defaultAuthProvider);
    }
  }
});
</script>
