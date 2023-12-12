<template>
  <file-drop-area @drop="importBtnRef?.performImport($event)" class="h-100">
    <full-height-page>
      <list-view ref="listViewRef" url="/api/v1/findingtemplates/">
        <template #title>Finding Templates</template>
        <template #searchbar="{items}">
          <v-row dense class="mb-2 w-100">
            <v-col cols="12" md="10">
              <v-text-field
                :model-value="items.search.value"
                @update:model-value="listViewRef?.updateSearchQuery"
                label="Search"
                spellcheck="false"
                hide-details="auto"
                variant="underlined"
                autofocus
                class="ma-0"
              />
            </v-col>
            <v-col cols="12" md="2">
              <s-language-selection
                v-model="currentLanguage"
                :items="languageChoices"
                variant="underlined"
                class="ma-0"
              />
            </v-col>
          </v-row>
        </template>
        <template #actions>
          <btn-create 
            to="/templates/new/" 
            :disabled="!auth.hasScope('template_editor')"
          />
          <btn-import 
            ref="importBtnRef"
            :import="performImport"
            :disabled="!auth.hasScope('template_editor')"
          />
        </template>
        <template #item="{item}">
          <template-list-item
            :template="item"
            :language="currentLanguage"
            :to="{path: `/templates/${item.id}/`, query: {language: currentLanguage}}"
            lines="two"
          />
        </template>
      </list-view>
    </full-height-page>
  </file-drop-area>
</template>

<script setup lang="ts">
definePageMeta({
  title: 'Templates',
  toplevel: true,
});
useHeadExtended({
  breadcrumbs: () => templateListBreadcrumbs(),
});

const route = useRoute();
const router = useRouter();
const apiSettings = useApiSettings();
const auth = useAuth();

const listViewRef = ref();

const languageChoices = computed(() => [{ code: null as string|null, name: 'All' }].concat(apiSettings.settings!.languages.filter(l => l.enabled || l.code === route.query.language)));
const currentLanguage = computed({
  get: () => (Array.isArray(route.query.language) ? route.query.language[0] : route.query.language) || null,
  set: (val) => {
    router.replace({ query: { ...route.query, language: val || '' } })
  }
});

const importBtnRef = ref();
async function performImport(file: File) {
  const templates = await uploadFileHelper<FindingTemplate[]>('/api/v1/findingtemplates/import/', file);
  await navigateTo(`/templates/${templates[0].id}/`)
}
</script>
