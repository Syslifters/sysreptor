<template>
  <v-container>
    <h1><slot name="title" /></h1>

    <v-text-field :value="items.searchQuery" @input="updateSearch" label="Search" spellcheck="false" />

    <slot name="actions" />
    <v-list v-if="items">
      <slot v-for="item in items.data" name="item" :item="item" />
      <div v-if="items.hasNextPage" v-intersect="(e, o, isIntersecting) => isIntersecting ? fetchNextPage() : null" class="text-center mt-5 -b">
        <v-progress-circular indeterminate />
      </div>
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
        searchFilters: { search: this.$route.query.search || null }, 
        axios: this.$axios, 
        toast: this.$toast
      }),
    }
  },
  async fetch() {
    await this.fetchNextPage();
  },
  watch: {
    '$route.query.search'(val) {
      this.items.search(val);
    }
  },
  methods: {
    updateSearch(search) {
      this.$router.replace({ query: { search: search || '' } });
      this.items.search(search);
    },
    async fetchNextPage() {
      return await this.items.fetchNextPageImmediate();
    }
  }
}
</script>
