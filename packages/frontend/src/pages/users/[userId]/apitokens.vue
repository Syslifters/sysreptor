<template>
  <s-card class="mt-4">
    <v-card-title>API Tokens</v-card-title>
    <v-card-text>
      <v-list>
        <v-list-item
          v-for="apiToken in apiTokens"
          :key="apiToken.id"
          prepend-icon="mdi-key-variant"
        >
          <v-list-item-title>
            {{ apiToken.name }}
            <api-token-scope :token="apiToken" />
            <v-chip
              v-if="apiToken.admin_permissions_enabled"
              size="small"
              class="ml-3"
            >
              Admin
            </v-chip>
            <chip-expires class="ml-3" :value="apiToken.expire_date" />
            <chip-date :value="apiToken.last_used" label="Last Used" />
            <chip-created :value="apiToken.created" />
          </v-list-item-title>
          <template #append>
            <btn-delete button-variant="icon" :delete="() => deleteApiToken(apiToken)" :disabled="!canEdit" />
          </template>
        </v-list-item>
        <v-list-item
          v-if="apiTokens.length === 0"
          title="No API tokens available"
        />
      </v-list>
    </v-card-text>
  </s-card>
</template>

<script setup lang="ts">
const route = useRoute();
const auth = useAuth();
const user = await useFetchE<User>(`/api/v1/pentestusers/${route.params.userId}/`, { method: 'GET' });
const apiTokens = await useAsyncDataE<ApiToken[]>(async () => {
  try {
    return await $fetch<ApiToken[]>(`/api/v1/pentestusers/${route.params.userId}/apitokens/`, { method: 'GET' });
  } catch (error: any) {
    if (error?.data?.code === 'reauth-required') {
      auth.redirectToReAuth({ authRedirect: route.fullPath, replace: true });
      return [];
    } else {
      throw error;
    }
  }
});
const canEdit = computed(() => !user.value.is_system_user && (
  (auth.hasPermission(UserPermission.USER_EDIT) && !user.value.is_superuser) ||
  auth.permissions.value.admin
));

async function deleteApiToken(apiToken: ApiToken) {
  await $fetch(`/api/v1/pentestusers/${route.params.userId}/apitokens/${apiToken.id}/`, { method: 'DELETE' });
  apiTokens.value = apiTokens.value.filter(t => t.id !== apiToken.id);
}
</script>
