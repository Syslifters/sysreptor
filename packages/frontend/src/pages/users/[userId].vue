<template>
  <split-menu>
    <template #menu>
      <v-list nav density="compact">
        <v-list-item-title class="text-h6 pl-2 mb-2">{{ user.username }}</v-list-item-title>

        <v-list-item
          :to="`/users/${user.id}/`" exact
          prepend-icon="mdi-account"
          title="User Information"
        />
        <v-list-item
          :disabled="!apiSettings.isLocalUserAuthEnabled"
          :to="`/users/${user.id}/reset-password/`"
          prepend-icon="mdi-form-textbox-password"
          title="Reset Password"
        />
        <v-list-item
          :disabled="!apiSettings.isLocalUserAuthEnabled"
          :to="`/users/${user.id}/mfa/`"
          prepend-icon="mdi-lock"
          title="Multi Factor Authentication"
        />
        <v-list-item
          :disabled="!apiSettings.isSsoEnabled"
          :to="`/users/${user.id}/identities/`"
          prepend-icon="mdi-card-account-details"
        >
          <v-list-item-title><pro-info>SSO Identities</pro-info></v-list-item-title>
        </v-list-item>
        <v-list-item
          :to="`/users/${user.id}/apitokens/`"
          prepend-icon="mdi-key-variant"
          title="API Tokens"
        />
      </v-list>
    </template>

    <template #default>
      <nuxt-page />
    </template>
  </split-menu>
</template>

<script setup lang="ts">
const route = useRoute();
const auth = useAuth();
const apiSettings = useApiSettings();
const user = await useFetchE<User>(`/api/v1/pentestusers/${route.params.userId}/`, { method: 'GET' });

useHeadExtended({
  breadcrumbs: () => userDetailBreadcrumbs(user.value),
});

await useAsyncData(async () => {
  if (!auth.permissions.value.user_manager) {
    await navigateTo('/');
  }
});
</script>
