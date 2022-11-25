<template>
  <div v-if="items.hasNextPage" class="text-center">
    <div v-if="!items.isLoading && !items.hasError" v-intersect="onIntersect" />

    <div v-if="items.hasError">
      <v-alert color="error">
        Failed to load data
        <template v-if="items.errorData?.detail">: {{ items.errorData.detail }}</template>
        <br>
        <s-btn 
          @click="fetchNextPage" 
          :loading="items.isLoading"
          color="secondary"
        >
          <v-icon>mdi-refresh</v-icon>
          Retry
        </s-btn>
      </v-alert>
    </div>
    <v-progress-circular v-else indeterminate />
  </div>
</template>

<script>
export default {
  props: {
    items: {
      type: Object,
      required: true,
    }
  },
  methods: {
    onIntersect(event, observer, isIntersecting) {
      if (isIntersecting) {
        this.fetchNextPage();
      }
    },
    async fetchNextPage() {
      if (this.items.fetchNextPageImmediate !== undefined) {
        return await this.items.fetchNextPageImmediate();
      } else {
        return await this.items.fetchNextPage();
      }
    },
  }
}
</script>
