<template>
  <file-drop-area @drop="importBtnRef?.performImport($event)" class="h-100">
    <list-view 
      ref="listViewRef" 
      url="/api/v1/findingtemplates/"
      v-model:ordering="localSettings.templateListOrdering"
      :ordering-options="[
        {id: 'risk', title: 'Severity', value: '-risk'},
        {id: 'created', title: 'Created', value: '-created'},
        {id: 'updated', title: 'Updated', value: '-updated'},
      ]"
    >
      <template #title>Templates</template>
      <template #searchbar="{ items, ordering, orderingOptions }">
        <v-row dense class="mb-2 w-100">
          <v-col cols="12" md="auto" class="flex-grow-1">
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
            <s-language-selection
              v-model="currentLanguage"
              :items="languageChoices"
              variant="underlined"
              class="ma-0"
            />
          </v-col>
          <v-col cols="auto">
            <s-select-ordering
              :model-value="ordering"
              @update:model-value="listViewRef?.updateOrdering"
              :ordering-options="orderingOptions"
            />
          </v-col>
        </v-row>
      </template>
      <template #actions>
        <btn-create 
          @click="performCreate"
          :disabled="!auth.permissions.value.template_editor"
          :loading="performCreateInProgress"
        />
        <btn-import 
          ref="importBtnRef"
          :import="performImport"
          :disabled="!auth.permissions.value.template_editor"
        />
      </template>
      <template #item="{item}: {item: FindingTemplate}">
        <template-list-item
          :template="item"
          :language="currentLanguage"
          :to="{path: `/templates/${item.id}/`, query: {language: currentLanguage}}"
          lines="two"
        />
      </template>
    </list-view>
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
const localSettings = useLocalSettings();
const apiSettings = useApiSettings();
const auth = useAuth();
const templateStore = useTemplateStore();

const listViewRef = ref();

const languageChoices = computed(() => [{ code: null as string|null, name: 'All' } as Language].concat(apiSettings.settings!.languages.filter(l => l.enabled || l.code === route.query.language)));
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

const performCreateInProgress = ref(false);
async function performCreate() {
  try {
    performCreateInProgress.value = true;
    const obj = await templateStore.create({
      tags: [],
      translations: [{
        is_main: true,
        language: apiSettings.settings!.languages[0]?.code || 'en-US',
        status: ReviewStatus.IN_PROGRESS,
        data: {
          title: 'TODO: New Template Title',
        },
      }],
    });
    await navigateTo(`/templates/${obj.id}/`);
  } catch (error) {
    requestErrorToast({ error });
  } finally {
    performCreateInProgress.value = false;
  }
}
</script>
