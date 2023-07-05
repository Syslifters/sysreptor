<template>
  <s-card class="mt-4">
    <v-card-title>API Tokens</v-card-title>
    <v-card-text>
      <v-list>
        <v-list-item v-for="apiToken in apiTokens" :key="apiToken.id">
          <v-list-item-icon>
            <v-icon>mdi-key-variant</v-icon>
          </v-list-item-icon>
          <v-list-item-title>
            {{ apiToken.name }}
            <chip-expires class="ml-3" :value="apiToken.expire_date" />
          </v-list-item-title>
          <v-list-item-action>
            <btn-delete icon :delete="() => deleteApiToken(apiToken)" />
          </v-list-item-action>
        </v-list-item>
        <v-list-item v-if="apiTokens.length === 0">
          <v-list-item-title>No API tokens available</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-card-text>
  </s-card>
</template>

<script>
export default {
  async asyncData({ $axios, params }) {
    return {
      apiTokens: await $axios.$get(`/pentestusers/${params.userId}/apitokens/`),
    };
  },
  methods: {
    async deleteApiToken(apiToken) {
      try {
        await this.$axios.$delete(`/pentestusers/self/apitokens/${apiToken.id}/`);
        this.apiTokens = this.apiTokens.filter(t => t.id !== apiToken.id);
      } catch (error) {
        this.$toast.global.requestError({ error });
      }
    },
  }
}
</script>
