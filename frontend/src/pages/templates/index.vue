<template>
  <file-drop-area @drop="importBtn.performImport($event)" class="h-100">
    <div class="h-100 overflow-y-auto">
      <list-view url="/api/v1/findingtemplates/">
        <template #title>Finding Templates</template>
        <template #searchbar="{items}">
          <v-row dense class="mb-2 w-100">
            <v-col cols="12" md="10">
              <v-text-field
                :model-value="items.search.value"
                @update:model-value="updateSearchQuery(items, $event)"
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
        <template #actions v-if="auth.hasScope('template_editor')">
          <s-btn
            to="/templates/new/"
            color="primary"
            prepend-icon="mdi-plus"
            text="Create"
            class="mr-1 ml-1"
          />
          <btn-import
            ref="importBtn"
            :import="performImport"
            class="mr-1 ml-1"
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
    </div>
  </file-drop-area>
</template>

<script setup lang="ts">
import { ReturnType } from "birpc";

definePageMeta({
  title: 'Templates',
});

const route = useRoute();
const router = useRouter();
const apiSettings = useApiSettings();
const auth = useAuth();

const importBtn = ref();

const languageChoices = computed(() => [{ code: null as string|null, name: 'All' }].concat(apiSettings.settings!.languages.filter(l => l.enabled || l.code === route.query.language)));
const currentLanguage = computed({
  get: () => (Array.isArray(route.query.language) ? route.query.language[0] : route.query.language) || null,
  set: (val) => {
    router.replace({ query: { ...route.query, language: val || '' } })
  }
});
function updateSearchQuery(items: ReturnType<typeof useSearchableCursorPaginationFetcher>, search: string) {
  items.search.value = search;
  router.replace({ query: { ...route.query, search: search || '' } });
}

async function performImport(file: File) {
  const templates = await uploadFileHelper<FindingTemplate[]>('/api/v1/findingtemplates/import/', file);
  await navigateTo(`/api/v1/templates/${templates[0].id}/`)
}
</script>
