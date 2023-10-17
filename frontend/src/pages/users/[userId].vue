<template>
  <split-menu :model-value="15">
    <template #menu>
      <v-list nav density="compact">
        <v-list-item-title class="text-h6 pl-2 mb-2">{{ user.username }}</v-list-item-title>

        <v-list-item
          :to="`/users/${user.id}/`" exact
          prepend-icon="mdi-account"
          title="User Information"
        />
        <v-list-item
          v-if="apiSettings.isLocalUserAuthEnabled"
          :to="`/users/${user.id}/reset-password/`"
          prepend-icon="mdi-form-textbox-password"
          title="Reset Password"
        />
        <v-list-item
          v-if="apiSettings.isLocalUserAuthEnabled"
          :to="`/users/${user.id}/mfa/`"
          prepend-icon="mdi-lock"
          title="Multi Factor Authentication"
        />
        <v-list-item
          v-if="apiSettings.isSsoEnabled"
          :to="`/users/${user.id}/identities/`"
          prepend-icon="mdi-card-account-details"
          title="SSO Identities"
        />
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
const apiSettings = useApiSettings();
const user = await useFetchE<User>(`/api/v1/pentestusers/${route.params.userId}/`, { method: 'GET' });
</script>
