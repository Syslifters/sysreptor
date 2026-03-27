<template>
  <full-height-page scrollbar>
    <v-container class="pt-0">
      <v-list
        v-if="items"
        v-bind="selection.listProps.value"
        class="pt-0 overflow-visible"
      >
        <div class="list-header pt-2">
          <div class="list-header-titlebar">
            <h1 class="text-headline-large font-weight-bold ma-0">
              <slot name="title" />
            </h1>

            <div v-if="$slots.navigation">
              <slot name="navigation" />
            </div>
            
            <div v-if="$slots.actions" class="list-header-actions">
              <slot
                name="actions"
                :items="items.data.value"
                :selected-items="selection.selectedItems.value as any"
              />
            </div>
          </div>
         
          <div class="searchbar mt-1">
            <slot name="searchbar" :items="items" :ordering="ordering" :ordering-options="orderingOptions" :filter-properties="filterProperties" :selection="selection">
              <div v-if="props.selectable" class="searchbar-prepend">
                <v-badge
                  v-if="props.selectable"
                  :content="allSelectedCount"
                  :model-value="allSelectedCount > 0"
                  floating
                  location="top left"
                  :offset-x="8"
                  :offset-y="16"
                >
                  <s-checkbox
                    :model-value="visibleSelectedAllItemsInCurrentPage"
                    @update:model-value="$event ? selection.selectAll() : selection.clearSelection({ onlyVisible: true })"
                    :indeterminate="visibleSelectedCount > 0 && !visibleSelectedAllItemsInCurrentPage"
                    :disabled="items.data.value.length === 0"
                    density="comfortable"
                    class="select-all-checkbox"
                  />
                  <s-tooltip activator="parent" location="top">
                    <span v-if="allSelectedCount === 0">Select all</span>
                    <span v-else-if="allSelectedCount === visibleSelectedCount">{{ allSelectedCount }} selected</span>
                    <span v-else>{{ allSelectedCount }} selected ({{ visibleSelectedCount }} visible)</span>
                  </s-tooltip>
                </v-badge>
              </div>

              <div class="searchbar-input flex-grow-width">
                <v-text-field
                  ref="searchbarRef"
                  :model-value="items.search.value"
                  @update:model-value="updateSearch"
                  label="Search"
                  variant="underlined"
                  spellcheck="false"
                  hide-details="auto"
                  autofocus
                  class="flex-grow-width"
                  clearable
                />

                <slot name="filters" :active-filters="activeFilters" :filter-properties="props.filterProperties">
                  <filter-chip-list
                    v-if="props.filterProperties && props.filterProperties.length > 0"
                    v-model="activeFilters"
                    :filter-properties="props.filterProperties"
                    @update-pinned="updatePinnedFilters"
                    class="filter-chip-list"
                  />
                </slot>
              </div>

              <div class="searchbar-append">
                <filter-chip-selector
                  v-if="props.filterProperties && props.filterProperties.length > 0"
                  v-model:active-filters="activeFilters"
                  :filter-properties="props.filterProperties"
                />
                <s-select-ordering
                  v-if="props.orderingOptions && props.orderingOptions.length > 0"
                  :model-value="ordering"
                  @update:model-value="updateOrdering"
                  :ordering-options="props.orderingOptions"
                />
              </div>
            </slot>
          </div>
        </div>

        <slot name="items" :items="items">
          <slot v-for="item in items.data.value" name="item" :item="item as any" />
        </slot>
        <page-loader :items="items" class="mt-4" />
        <v-list-item
          v-if="items.data.value.length === 0 && !items.hasNextPage.value && items.hasBaseURL.value"
          title="No data found"
          class="no-data-item"
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
import { pick, isEqual, sortBy, omit } from 'lodash-es';
import type { FilterProperties, FilterValue } from '@base/utils/types';
import { addFilter as addFilterUtil, filtersToQueryParams, parseFiltersFromQuery } from '@base/utils/filter';
import { useListSelection } from '@base/composables/listselection';

const orderingModel = defineModel<string|null>('ordering');
const props = defineProps<{
  url: string|null;
  orderingOptions?: OrderingOption[];
  filterProperties?: FilterProperties[];
  selectable?: boolean;
}>();

const pinnedFilters = defineModel<FilterValue[]>('pinnedFilters');
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

const selection = useListSelection<T & { id: string }>({
  items: items.data as unknown as MaybeRefOrGetter<(T & { id: string})[]>,
  enabled: () => props.selectable,
});
const allSelectedCount = computed(() => selection.selectedItems.value.length);
const visibleSelectedCount = computed(() => selection.selectedItemsVisible.value.length);
const visibleSelectedAllItemsInCurrentPage = computed(() => selection.enabled.value && items.data.value.length > 0 && visibleSelectedCount.value === items.data.value.length);

onMounted(async () => {
  if (!props.filterProperties || props.filterProperties.length === 0) {
    return;
  }

  const pinnedFiltersParsed = Array.isArray(pinnedFilters.value) ? pinnedFilters.value.filter(f => props.filterProperties?.some(fp => fp.id === f.id)) : [];

  // If URL filters are present, respect them (they override pinned defaults)
  const filtersFromUrl = parseFiltersFromQuery(route.query, props.filterProperties);
  if (filtersFromUrl && filtersFromUrl.length > 0) {
    activeFilters.value = filtersFromUrl;
  } else {
    // No explicit URL filters: apply pinned filters
    activeFilters.value = pinnedFiltersParsed.map(f => ({...f}));
  }

  for (const f of activeFilters.value) {
    f.internalId = uuidv4();
    if (pinnedFilters.value) {
      // Set filter.isPinned for pinned filters. Apply both for URL and pinned filters
      f.isPinned = pinnedFiltersParsed.some(pf => isEqual(omit(pf, ['internalId', 'isPinned']), omit(f, ['internalId', 'isPinned'])));
    }
  }
  // Sort filters: pinned first
  activeFilters.value = sortBy(activeFilters.value, [f => !f.isPinned, f => pinnedFiltersParsed.findIndex(pf => isEqual(omit(pf, ['internalId', 'isPinned']), omit(f, ['internalId', 'isPinned'])))]);
});

// Watch for filter changes and update URL
watch(activeFilters, () => {
  for (const f of activeFilters.value) {
    f.internalId ??= uuidv4();
    if (pinnedFilters.value) {
      f.isPinned ??= false;
    }
  }

  if (props.filterProperties && props.filterProperties.length > 0) {
    const filterParams = filtersToQueryParams(activeFilters.value, props.filterProperties);

    router.replace({
      query: {
        ...pick(route.query, ['search']),
        ordering: ordering.value?.value || '',
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

const searchbarRef = useTemplateRef('searchbarRef');
useHotkey('ctrl+f', () => searchbarRef.value?.focus(), { inputs: true });
function updateSearch(search: string) {
  items.search.value = search;
  router.replace({ query: { ...route.query, ordering: ordering.value?.value || '', search } });
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

function updatePinnedFilters() {
  // When any filter is pinned or unpinned, update the entire list of pinned filters to the currently pinned filters
  if (pinnedFilters.value && props.filterProperties) {
    pinnedFilters.value = activeFilters.value.filter(f => f.isPinned).map(f => omit(f, ['internalId', 'isPinned']));
  }
}

async function refresh() {
  selection.clearSelection({ onlyVisible: false });
  items.reset({
    query: {
      ordering: ordering.value?.value,
    },
  });
  await items.fetchNextPage();
}

defineExpose({
  items,
  selection,
  activeFilters,
  updateSearch,
  updateOrdering,
  addFilter,
  refresh,
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

.list-header-titlebar {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
}
.list-header-actions {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0.3rem;
}

.searchbar {
  display: flex;
  flex-direction: row;

  &-prepend {
    padding-inline-start: 10px;
    padding-inline-end: 10px;
  }
}

.filter-chip-list:deep(.v-chip) {
  margin-top: 0.2em;
  margin-bottom: 0.2em;
}
.select-all-checkbox:deep(.v-icon) {
  opacity: 1;
}

:deep(.v-list-item) {
  .v-list-item-subtitle {
    opacity: var(--v-high-emphasis-opacity);
  }

  .v-list-item-action .v-checkbox-btn {
    opacity: 0;
    transition: opacity 0.2s ease-in-out;
  }
  &:hover, &.v-list-item--active {
    .v-list-item-action .v-checkbox-btn {
      opacity: 1;
    }
  }
}

.no-data-item {
  pointer-events: none;
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
