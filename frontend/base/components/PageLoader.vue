<template>
  <div v-if="props.items.hasNextPage.value" class="text-center">
    <div v-if="!props.items.pending.value && !props.items.hasError.value" v-intersect="onIntersect" />

    <div v-if="props.items.hasError.value">
      <v-alert color="error">
        Failed to load data
        <template v-if="props.items.error.value?.detail">: {{ props.items.error.value.detail }}</template>
        <br>
        <s-btn-secondary
          @click="props.items.fetchNextPage()"
          :loading="props.items.pending.value"
          prepend-icon="mdi-refresh"
          text="Retry"
        />
      </v-alert>
    </div>
    <v-progress-circular v-else indeterminate />
  </div>
</template>

<script setup lang="ts" generic="T">
import type { useSearchableCursorPaginationFetcher } from "#imports";

const props = defineProps<{
  items: ReturnType<typeof useCursorPaginationFetcher> | ReturnType<typeof useSearchableCursorPaginationFetcher>;
}>();

function onIntersect(isIntersecting: boolean) {
  if (isIntersecting) {
    props.items.fetchNextPage();
  }
}
</script>
