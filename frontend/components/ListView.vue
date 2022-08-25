<template>
  <v-container>
    <h1><slot name="title" /></h1>

    <v-text-field :value="items.searchQuery" @input="updateSearch" label="Search" />

    <slot name="actions" />
    <v-list v-if="items">
      <slot v-for="item in items.data" name="item" :item="item" />
      <div v-if="items.hasNextPage" v-intersect="items.fetchNextPageImmediate" class="text-center mt-5 -b">
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
        searchQuery: this.$route.query.search || null, 
        axios: this.$axios, 
        toast: this.$toast
      }),
    }
  },
  async fetch() {
    await this.items.fetchNextPageImmediate();
  },
  watch: {
    '$route.query.search'(val) {
      this.items.search(val);
    }
  },
  methods: {
    updateSearch(search) {
      this.$router.replace({ path: './', query: { search: search || '' } });
      this.items.search(search);
    },
  }
}
</script>
