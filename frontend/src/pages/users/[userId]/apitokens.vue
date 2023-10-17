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
            <chip-expires class="ml-3" :value="apiToken.expire_date" />
          </v-list-item-title>
          <template #append>
            <btn-delete button-variant="icon" :delete="() => deleteApiToken(apiToken)" />
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
import { ApiToken } from "~/utils/types";

const route = useRoute();
const apiTokens = await useFetchE<ApiToken[]>(`/api/v1/pentestusers/${route.params.userId}/apitokens/`, { method: 'GET' });

async function deleteApiToken(apiToken: ApiToken) {
  try {
    await $fetch(`/api/v1/pentestusers/self/apitokens/${apiToken.id}/`, { method: 'GET' });
    apiTokens.value = apiTokens.value.filter(t => t.id !== apiToken.id);
  } catch (error) {
    requestErrorToast({ error });
  }
}
</script>
