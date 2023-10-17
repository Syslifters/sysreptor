<template>
  <split-menu v-model="localSettings.templateInputMenuSize">
    <template #menu>
      <template-field-selector />
    </template>

    <template #default>
      <fetch-loader v-bind="fetchLoaderAttrs">
        <template-editor
          ref="templateEditor"
          v-if="template"
          :model-value="template"
          :toolbar-attrs="toolbarAttrs"
          :rewrite-file-url="rewriteFileUrl"
          :readonly="true"
          :initial-language="template!.translations.find(tr => tr.id === route.query?.translation_id)?.language || route.query?.language"
          :history="true"
        >
          <template #toolbar-actions>
            <s-btn
              color="secondary"
              :to="`/templates/${template!.id}/`" exact
              class="ml-1 mr-1"
              prepend-icon="mdi-undo"
              text="Back to current version"
            />
          </template>
        </template-editor>
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

const baseUrl = computed(() => `/api/v1/findingtemplates/${route.params.templateId}/history/${route.params.historyDate}/`);

const fetchState = useLazyAsyncData<FindingTemplate>(async () => {
  const [template] = await Promise.all([
    $fetch<FindingTemplate>(baseUrl.value, { method: 'GET' }),
    templateStore.getFieldDefinition(),
  ]);
  return template;
});
const template = computed(() => fetchState.data.value);
const mainTranslation = computed(() => template.value?.translations?.find(tr => tr.is_main));

const title = computed(() => mainTranslation.value?.data?.title || null);
useHead({
  title
});

const vm = getCurrentInstance();
const toolbarRef = computed(() => vm?.refs?.templateEditor?.toolbarRef);
const { toolbarAttrs, fetchLoaderAttrs } = useLockEdit({
  data: fetchState.data,
  fetchState,
  baseUrl,
  toolbarRef,
  hasEditPermissions: computed(() => false),
  errorMessage: computed(() => `This is a historical version from ${formatISO9075(new Date(route.params.historyDate as string))}.`),
});

function rewriteFileUrl(imgSrc: string) {
  return urlJoin(baseUrl.value, imgSrc);
}
</script>
