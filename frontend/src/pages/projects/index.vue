<template>
  <file-drop-area @drop="importBtn.performImport($event)" class="h-100">
    <full-height-page>
      <template #header>
        <s-sub-menu>
          <v-tab :to="`/projects/`" exact text="Projects" />
          <v-tab :disabled="!apiSettings.settings!.features.archiving" to="/projects/archived/" text="Archived Projects" />
        </s-sub-menu>
      </template>

      <list-view ref="listViewRef" :url="apiUrl">
        <template #title>Projects</template>
        <template #actions>
          <btn-create to="/projects/new/" :disabled="!canCreate" />
          <btn-import ref="importBtn" :import="performImport" :disabled="!canImport" />
        </template>
        <template #searchbar="{items}">
          <v-row dense class="mb-2 w-100">
            <v-col cols="12" md="10">
              <v-text-field
                :model-value="items.search.value"
                @update:model-value="listViewRef?.updateSearch"
                label="Search"
                spellcheck="false"
                hide-details="auto"
                variant="underlined"
                autofocus
                class="ma-0"
              />
            </v-col>
            <v-col cols="12" md="2">
              <s-select 
                v-model="projectStateFilter"
                :items="[{ title: 'All Projects', value: ProjectStateFilter.ALL }, { title: 'Active Projects', value: ProjectStateFilter.ACTIVE }, { title: 'Finished Projects', value: ProjectStateFilter.FINISHED }]"
                label="State"
                variant="underlined"
                class="ma-0"
              />
            </v-col>
          </v-row>
        </template>
        <template #item="{item}">
          <v-list-item :to="`/projects/${item.id}/reporting/`" lines="two">
            <v-list-item-title>{{ item.name }}</v-list-item-title>

            <v-list-item-subtitle class="mt-1">
              <v-chip v-if="item.readonly" size="small" class="ma-1">
                <v-icon size="small" start icon="mdi-flag-checkered" />
                Finished
              </v-chip>
              <chip-created :value="item.created" />
              <chip-member v-for="user in item.members" :key="user.id" :value="user" />
              <chip-member v-for="user in item.imported_members" :key="user.id" :value="user" imported />
              <chip-tag v-for="tag in item.tags" :key="tag" :value="tag" />
            </v-list-item-subtitle>
          </v-list-item>
        </template>
      </list-view>
    </full-height-page>
  </file-drop-area>
</template>

<script setup lang="ts">
definePageMeta({
  title: 'Projects',
  toplevel: true,
});
useHeadExtended({
  breadcrumbs: () => projectListBreadcrumbs(),
});

const route = useRoute();
const router = useRouter();
const auth = useAuth();
const apiSettings = useApiSettings();

const listViewRef = ref();

enum ProjectStateFilter {
  ALL = 'all',
  ACTIVE = 'active',
  FINISHED = 'finished',
};

const projectStateFilter = computed<ProjectStateFilter>({
  get: () => route.query.state as any || ProjectStateFilter.ACTIVE,
  set: (val) => {
    router.replace({ query: { ...route.query, state: val } });
  }
});
const apiUrl = computed(() => {
  let apiUrl = "/api/v1/pentestprojects/";
  if (projectStateFilter.value === ProjectStateFilter.ACTIVE) {
    apiUrl += '?readonly=false';
  } else if (projectStateFilter.value === ProjectStateFilter.FINISHED) {
    apiUrl += '?readonly=true';
  }
  return apiUrl
})

const canCreate = computed(() => {
  if (auth.user.value!.is_guest && !apiSettings.settings!.guest_permissions.create_projects) {
    return false;
  }
  return true;
})
const canImport = computed(() => {
  if (auth.user.value!.is_guest && !apiSettings.settings!.guest_permissions.import_projects) {
    return false;
  }
  return true;
});

const importBtn = ref();
async function performImport(file: File) {
  const projects = await uploadFileHelper<PentestProject[]>('/api/v1/pentestprojects/import/', file);
  await navigateTo(`/projects/${projects[0].id}/`);
}
</script>
