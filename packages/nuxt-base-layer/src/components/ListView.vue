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

          <slot name="searchbar" :items="items" :ordering="ordering" :ordering-options="orderingOptions" :filter-properties="filterProperties">
            <div class="d-flex flex-row">
              <filter-chip-selector
                v-if="props.filterProperties && props.filterProperties.length > 0"
                v-model:active-filters="activeFilters"
                :filter-properties="props.filterProperties"
                class="mr-1"
              />
              <v-text-field
                :model-value="items.search.value"
                @update:model-value="updateSearch"
                label="Search"
                variant="underlined"
                spellcheck="false"
                hide-details="auto"
                autofocus
                class="mt-0 mb-2"
                clearable
              />
              <s-select-ordering
                v-if="props.orderingOptions && props.orderingOptions.length > 0"
                :model-value="ordering"
                @update:model-value="updateOrdering"
                :ordering-options="props.orderingOptions"
                class="ml-1"
              />
            </div>
          </slot>
          <slot name="filters" :active-filters="activeFilters" :filter-properties="props.filterProperties">
            <filter-chip-list
              v-if="props.filterProperties && props.filterProperties.length > 0"
              v-model="activeFilters"
              :filter-properties="props.filterProperties"
            />
          </slot>
          <v-tabs v-if="$slots.tabs" height="30" selected-class="text-primary" class="list-header-tabs">
            <slot name="tabs" />
          </v-tabs>
        </div>

        <slot name="items" :items="items">
          <slot v-for="item in items.data.value" name="item" :item="item as any" />
        </slot>
        <page-loader :items="items" class="mt-4" />
        <v-list-item
          v-if="items.data.value.length === 0 && !items.hasNextPage.value && items.hasBaseURL.value"
          title="No data found"
        >
          <div class="w-100 text-center">
            <img src="@base/assets/dino/notfound.svg" alt="" class="img-raptor" />
          </div>
        </v-list-item>
      </v-list>
    </v-container>
  </full-height-page>
</template>

<script setup lang="ts" generic="T">
import { pick } from 'lodash-es';
import type { FilterProperties, FilterValue } from '@base/utils/types';
import { addFilter as addFilterUtil, filtersToQueryParams, parseFiltersFromQuery } from '@base/utils/filter';

const orderingModel = defineModel<string|null>('ordering');
const props = defineProps<{
  url: string|null;
  orderingOptions?: OrderingOption[];
  filterProperties?: FilterProperties[];
}>();

// Filter-related state
const activeFilters = ref<FilterValue[]>([]);

const ordering = computed(() => {
  if (route.query.ordering) {
    return props.orderingOptions?.find(o => o.value === route.query.ordering) || null;
  } else {
    return props.orderingOptions?.find(o => o.id === orderingModel.value) || props.orderingOptions?.[0] || null
  }
});

const router = useRouter();
const route = useRoute();
const items = useSearchableCursorPaginationFetcher<T>({
  baseURL: props.url,
  query: { 
    ordering: ordering.value?.value,
    ...route.query 
  },
});
useLazyAsyncData(async () => {
  await items.fetchNextPage()
});

// Initialize filters from URL on mount
onMounted(async () => {
  if (props.filterProperties && props.filterProperties.length > 0) {
    const filtersFromUrl = parseFiltersFromQuery(route.query, props.filterProperties);
    if (filtersFromUrl.length > 0) {
      activeFilters.value = filtersFromUrl;
    }
  }
});

// Watch for filter changes and update URL
watch(activeFilters, () => {
  if (props.filterProperties && props.filterProperties.length > 0) {
    const filterParams = filtersToQueryParams(activeFilters.value, props.filterProperties);
    
    router.replace({
      query: {
        ...pick(route.query, ['search', 'ordering']),
        ...filterParams,
      }
    });
  }
}, { deep: true });

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

function updateOrdering(ordering?: OrderingOption|null) {
  orderingModel.value = ordering?.id || null;
  if (!ordering) {
    ordering = props.orderingOptions![0];
  } 
  router.replace({ query: { ...route.query, ordering: ordering?.value || '' } });
  items.applyFilters({ ...route.query });
}

function addFilter(filter: FilterValue) {
  addFilterUtil(activeFilters.value, filter);
}

defineExpose({
  items,
  activeFilters,
  updateSearch,
  updateOrdering,
  addFilter,
});
</script>

<style lang="scss" scoped>
@use "@base/assets/vuetify.scss" as vuetify;
.list-header {
  position: sticky;
  top: 0;
  z-index: 10;
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

.list-header h1 {
  min-height: 2em;
}

:deep(.v-list-item .v-list-item-subtitle) {
  opacity: var(--v-high-emphasis-opacity);
}

.img-raptor {
  width: 30em;
  max-width: 50%;
  max-height: 40vh;
  margin-top: 1rem;
  margin-left: auto;
  margin-right: auto;
  pointer-events: none;
  user-select: none;
}
</style>
