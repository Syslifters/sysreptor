<template>
  <s-autocomplete
    v-model="model"
    v-model:search="items.search.value"
    :items="allItems"
    :loading="items.pending.value"
    item-title="name"
    item-value="id"
    persistent-hint
    multiple
    chips
    closable-chips
    clearable
    return-object
    no-filter
    :hide-no-data="false"
  >
    <template #append-item v-if="allItems.length > 0">
      <page-loader :items="items" />
    </template>
    <template #no-data>
      <page-loader v-if="allItems.length === 0 && items.hasNextPage.value" :items="items" />
      <v-list-item v-else title="No projects found" />
    </template>
  </s-autocomplete>
</template>

<script setup lang="ts">
import { uniqBy } from "lodash-es";

type ProjectChoice = Pick<PentestProject, 'id' | 'name'>;

const model = defineModel<ProjectChoice[]>({ default: () => [] });
const props = defineProps<{
  queryFilters?: object,
}>();

const items = useSearchableCursorPaginationFetcher<ProjectChoice>({
  baseURL: '/api/v1/pentestprojects/',
  query: {
    ordering: 'name',
    ...props.queryFilters,
  },
});

const initialProjects = ref<ProjectChoice[]>([]);
useLazyAsyncData(async () => {
  if (model.value?.length) {
    initialProjects.value = model.value;
  }
});

const allItems = computed(() => uniqBy(initialProjects.value.concat(model.value || [], items.data.value), 'id'));
</script>
