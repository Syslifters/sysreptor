<template>
  <split-menu v-model="localSettings.templateInputMenuSize">
    <template #menu>
      <template-field-selector :visible-field-ids="visibleFieldIds" />
    </template>

    <template #default>
      <fetch-loader v-bind="fetchLoaderAttrs">
        <template-editor-diff
          v-if="fetchState.data.value"
          v-bind="editorDiffAttrs"
        >
          <template #toolbar-actions>
            <s-btn-secondary
              :to="`/templates/${fetchState.data.value.templateCurrent!.id}/`" exact
              class="ml-1 mr-1"
              prepend-icon="mdi-undo"
              text="Back to current version"
            />
          </template>
        </template-editor-diff>
      </fetch-loader>
    </template>
  </split-menu>
</template>

<script setup lang="ts">
import urlJoin from "url-join";
import { formatISO9075 } from "date-fns";

const route = useRoute();
const localSettings = useLocalSettings();
const templateStore = useTemplateStore();

const baseUrlHistoric = computed(() => `/api/v1/findingtemplates/${route.params.templateId}/history/${route.params.historyDate}/`);
const baseUrlCurrent = computed(() => `/api/v1/findingtemplates/${route.params.templateId}/`);

const fetchState = useLazyAsyncData(async () => {
  const [templateCurrent, templateHistoric] = await Promise.all([
    $fetch<FindingTemplate>(baseUrlCurrent.value, { method: 'GET' }),
    $fetch<FindingTemplate>(baseUrlHistoric.value, { method: 'GET' }),
    templateStore.getFieldDefinition(),
  ]);
  return {
    templateCurrent,
    templateHistoric,
  };
});
const visibleFieldIds = computed(() => {
  // Show only fields that are used in any translation. Hide unused fields.
  const fieldIdsInUse = ['title']
    .concat(fetchState.data.value?.templateHistoric.translations?.flatMap(tr => Object.entries(tr.data).filter(([_id, val]) => !!val).map(([id, _val]) => id)) || [])
    .concat(fetchState.data.value?.templateCurrent.translations?.flatMap(tr => Object.entries(tr.data).filter(([_id, val]) => !!val).map(([id, _val]) => id)) || []);
  return templateStore.fieldDefinitionList.filter(d => fieldIdsInUse.includes(d.id)).map(d => d.id);
});

function rewriteFileUrlHistoric(imgSrc: string) {
  return urlJoin(baseUrlHistoric.value, imgSrc);
}
function rewriteFileUrlCurrent(imgSrc: string) {
  return urlJoin(baseUrlCurrent.value, imgSrc);
}

const fetchLoaderAttrs = computed(() => ({
  fetchState: {
    data: fetchState.data.value,
    error: fetchState.error.value,
    pending: fetchState.pending.value,
  },
}));
const editorDiffAttrs = computed(() => ({
  historic: {
    value: fetchState.data.value?.templateHistoric,
    rewriteFileUrl: rewriteFileUrlHistoric,
  },
  current: {
    value: fetchState.data.value?.templateCurrent,
    rewriteFileUrl: rewriteFileUrlCurrent,
  },
  initialLanguage: route.query?.language as string,
  toolbarAttrs: {
    data: fetchState.data.value?.templateHistoric,
    editMode: EditMode.READONLY,
    errorMessage: `This is a historic version from ${formatISO9075(new Date(route.params.historyDate as string))}.`,
  },
  visibleFieldIds: visibleFieldIds.value,
  historyDate: route.params.historyDate as string,
}));
useHeadExtended({
  title: computed(() => {
    const mainTranslation = fetchState.data.value?.templateCurrent?.translations?.find(tr => tr.is_main);
    return mainTranslation?.data.title || null;
  }),
  breadcrumbs: () => templateDetailBreadcrumbs(fetchState.data.value?.templateCurrent),
});
</script>
