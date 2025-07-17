<template>
  <list-view
    ref="listViewRef"
    url="/api/v1/archivedprojects/"
    :filter-properties="filterProperties"
  >
    <template #title>Projects</template>
    <template #tabs>
      <v-tab :to="{path: '/projects/', query: route.query}" exact prepend-icon="mdi-file-document" text="Active" />
      <v-tab :to="{path: '/projects/finished/', query: route.query}" prepend-icon="mdi-flag-checkered" text="Finished" />
      <v-tab :to="{path: '/projects/archived/', query: route.query}" prepend-icon="mdi-folder-lock-outline" text="Archived" />
    </template>
    <template #item="{item}: { item: ArchivedProject}">
      <v-list-item :to="`/projects/archived/${item.id}/`" lines="two">
        <v-list-item-title> {{ item.name }}</v-list-item-title>

        <v-list-item-subtitle>
          <chip-storage-size :value="item.size" />

          <chip-created :value="item.created" />
          <chip-auto-delete :value="item.auto_delete_date" />

          <v-chip size="small" class="ma-1">
            <v-icon v-if="item.key_parts.some(p => !p.user.is_active) && item.key_parts.filter(p => p.user.is_active).length < item.threshold * 2" size="small" start color="warning" icon="mdi-alert" />
            {{ item.threshold }} / {{ item.key_parts.length }}

            <s-tooltip activator="parent">
              {{ item.threshold }} of {{ item.key_parts.length }} users are required to restore this project
            </s-tooltip>
          </v-chip>

          <v-chip
            v-for="keypart in item.key_parts" :key="keypart.id"
            class="ma-1" size="small"
          >
            <v-icon v-if="keypart.is_decrypted" size="small" start color="success" icon="mdi-lock-open-variant" />
            <v-icon v-else size="small" start color="red" icon="mdi-lock" />
            {{ keypart.user.username }}

            <s-tooltip activator="parent">
              <span v-if="keypart.is_decrypted">{{ keypart.user.username }} already restored their part</span>
              <span v-else>{{ keypart.user.username }}'s part is still encrypted</span>
            </s-tooltip>
          </v-chip>

          <chip-tag
            v-for="tag in item.tags"
            :key="tag"
            :value="tag"
            class="mt-2"
            :filterable="true"
            @filter="listViewRef?.addFilter($event)"
          />
        </v-list-item-subtitle>
      </v-list-item>
    </template>
  </list-view>
</template>

<script setup lang="ts">
import { sortBy, uniq } from 'lodash-es';

definePageMeta({
  title: 'Projects',
  toplevel: true,
});
useHeadExtended({
  breadcrumbs: () => archivedProjectListBreadcrumbs(),
});

const route = useRoute();

const listViewRef = useTemplateRef('listViewRef');
const suggestedTags = ref<string[]>([]);
watch(() => listViewRef.value?.items?.data.value as ArchivedProject[]|undefined, (items) => {
  if (!items) { return; }
  suggestedTags.value = sortBy(uniq(items.flatMap(p => p.tags).concat(suggestedTags.value)));
}, { immediate: true, deep: 1 });
const filterProperties = computed((): FilterProperties[] => [
  { id: 'tag', name: 'Tag', icon: 'mdi-tag', type: 'combobox', options: suggestedTags.value, allow_exclude: true, allow_regex: false, default: '', multiple: true },
  { id: 'timerange', name: 'Time Archived', icon: 'mdi-calendar', type: 'daterange', options: [], allow_exclude: true, default: '', multiple: true },
]);
</script>
