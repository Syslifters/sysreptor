<template>
  <s-autocomplete
    v-model="model"
    v-model:search="items.search.value"
    :items="allItems"
    :loading="items.pending.value"
    item-title="name"
    item-value="id"
    label="Restrict to projects (optional)"
    hint="Leave empty for unrestricted access. Selected projects also grant read access to the global finding-template library."
    persistent-hint
    multiple
    chips
    closable-chips
    clearable
    return-object
    no-filter
    :hide-no-data="false"
    @update:menu="onMenu"
  >
    <template #append-item><page-loader :items="items" /></template>
    <template #no-data>
      <page-loader v-if="items.hasNextPage.value" :items="items" />
      <v-list-item v-else title="No projects found" />
    </template>
  </s-autocomplete>
</template>

<script setup lang="ts">
import { uniqBy } from 'lodash-es';

type ProjectChoice = Pick<PentestProject, 'id' | 'name'>;
const model = defineModel<ProjectChoice[]>({ default: () => [] });
const auth = useAuth();
// Match token creation permissions without the session's elevated admin mode.
const query = new URLSearchParams({ ordering: 'name' });
if (!auth.user.value!.is_project_admin) {
  query.set('member', auth.user.value!.username);
}
const items = useSearchableCursorPaginationFetcher<ProjectChoice>({
  baseURL: `/api/v1/pentestprojects/?${query}`,
});
const allItems = computed(() => uniqBy([...(model.value || []), ...items.data.value], 'id'));

function onMenu(open: boolean) {
  if (open && items.data.value.length === 0) {
    items.fetchNextPage();
  }
}
</script>
