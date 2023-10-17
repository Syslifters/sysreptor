<template>
  <v-container class="pt-0">
    <v-list v-if="items" class="pt-0 overflow-visible">
      <div class="list-header pt-2 mb-4">
        <h1><slot name="title" /></h1>

        <slot name="searchbar" :items="items">
          <v-text-field
            :model-value="items.search.value"
            @update:model-value="updateSearch"
            label="Search"
            variant="underlined"
            spellcheck="false"
            hide-details="auto"
            autofocus
            class="mt-0 mb-2"
          />
        </slot>

        <slot name="actions" />
      </div>

      <slot v-for="item in items.data.value" name="item" :item="item" />
      <page-loader :items="items" class="mt-4" />
      <v-list-item
        v-if="items.data.value.length === 0 && !items.hasNextPage.value"
        text="No data found"
      />
    </v-list>
  </v-container>
</template>

<script setup lang="ts" generic="T">
import { useSearchableCursorPaginationFetcher } from "~/composables/api";

const props = defineProps<{
  url: string
}>();

const router = useRouter();
const route = useRoute();
const items = useSearchableCursorPaginationFetcher<T>({
  baseURL: props.url,
  query: { ...route.query },
});
useLazyAsyncData(async () => {
  await items.fetchNextPage()
});

watch(() => route.query, () => {
  items.applyFilters({ ...route.query }, { debounce: true });
}, { deep: true });

function updateSearch(search: string) {
  items.search.value = search;
  router.replace({ query: { ...route.query, search } });
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
