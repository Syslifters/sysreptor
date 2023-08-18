<template>
  <v-container class="pt-0">
    <v-list v-if="items" class="pt-0">
      <div class="list-header pt-2">
        <h1><slot name="title" /></h1>

        <slot name="searchbar" :items="items">
          <v-text-field 
            :value="items.searchQuery" 
            @input="updateSearch" 
            label="Search" 
            spellcheck="false" 
            hide-details="auto" 
            autofocus
            class="mt-0 mb-2"
          />
        </slot>

        <slot name="actions" />
      </div>

      <slot v-for="item in items.data" name="item" :item="item" />
      <page-loader :items="items" />
      <v-list-item v-if="items.data.length === 0 && !items.hasNextPage">
        <v-list-item-title>
          No data found
        </v-list-item-title>
      </v-list-item>
    </v-list>
  </v-container>
</template>

<script>
import { SearchableCursorPaginationFetcher } from '~/utils/urls'

export default {
  props: {
    url: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      items: new SearchableCursorPaginationFetcher({
        baseURL: this.url, 
        searchFilters: { ...this.$route.query },
        axios: this.$axios, 
        toast: this.$toast
      }),
    }
  },
  async fetch() {
    await this.fetchNextPage();
  },
  watch: {
    '$route.query': {
      deep: true,
      handler() {
        this.items.applyFilters({ ...this.$route.query });
      }
    },
  },
  methods: {
    updateSearch(search) {
      this.items.search(search);
      this.$router.replace({ query: { ...this.$route.query, search: search || '' } });
    },
    async fetchNextPage() {
      return await this.items.fetchNextPageImmediate();
    }
  }
}
</script>

<style lang="scss" scoped>
.list-header {
  position: sticky;
  top: 0;
  z-index: 1;
  background-color: white;
}
</style>
