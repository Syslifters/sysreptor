<template>
  <full-height-page scrollbar>
    <v-container class="pt-0">
      <v-list v-if="items" class="pt-0 overflow-visible">
        <div class="list-header pt-2 mb-4">
          <h1>
            <slot name="title" />

            <div v-if="$slots.actions" class="list-header-actions">
              <slot name="actions" />
            </div>
          </h1>

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
          <v-tabs v-if="$slots.tabs" height="30" selected-class="text-primary" class="list-header-tabs">
            <slot name="tabs" />
          </v-tabs>
        </div>

        <slot v-for="item in items.data.value" name="item" :item="item" />
        <page-loader :items="items" class="mt-4" />
        <v-list-item
          v-if="items.data.value.length === 0 && !items.hasNextPage.value"
          title="No data found"
        />
      </v-list>
    </v-container>
  </full-height-page>
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
watch(() => props.url, async () => {
  items.reset({ baseURL: props.url, query: { ...route.query } });
  await items.fetchNextPage();
});

function updateSearch(search: string) {
  items.search.value = search;
  router.replace({ query: { ...route.query, search } });
}

defineExpose({
  items,
  updateSearch,
});
</script>

<style lang="scss" scoped>
@use "@/assets/vuetify.scss" as vuetify;
.list-header {
  position: sticky;
  top: 0;
  z-index: 1;
  background-color: vuetify.$list-background;
}
.list-header-actions {
  margin-left: 1rem;
  display: inline-block;
  
  &:deep() > * {
    margin-left: 0.5rem;
  }
}

.list-header-tabs:deep(.v-tab) {
  text-transform: initial;
}
</style>
