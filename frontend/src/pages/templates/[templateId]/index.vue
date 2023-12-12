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
          v-model="template"
          :toolbar-attrs="{...toolbarAttrs, canAutoSave: true}"
          :upload-file="uploadFile"
          :rewrite-file-url="rewriteFileUrl"
          :readonly="readonly"
          :initial-language="template!.translations.find(tr => tr.id === route.query?.translation_id)?.language || route.query?.language"
          :history="true"
        >
          <template #toolbar-context-menu v-if="auth.hasScope('template_editor')">
            <btn-export
              :export-url="`/api/v1/findingtemplates/${template.id}/export/`"
              :name="`template-` + mainTranslation!.data.title"
            />
          </template>
        </template-editor>
      </fetch-loader>
    </template>
  </split-menu>
</template>

<script setup lang="ts">
import isEqual from "lodash/isEqual";
import urlJoin from "url-join";
import { uploadFileHelper } from "~/utils/upload";

const route = useRoute();
const auth = useAuth();
const localSettings = useLocalSettings();
const templateStore = useTemplateStore();

const baseUrl = computed(() => `/api/v1/findingtemplates/${route.params.templateId}/`);

const fetchState = useLazyAsyncData<FindingTemplate>(async () => {
  const [template] = await Promise.all([
    $fetch<FindingTemplate>(baseUrl.value, { method: 'GET' }),
    templateStore.getFieldDefinition(),
  ]);
  return template;
});
const template = computed({
  get: () => fetchState.data.value,
  set: (val) => {
    fetchState.data.value = val
  }
});
const mainTranslation = computed(() => template.value?.translations?.find(tr => tr.is_main));

const title = computed(() => mainTranslation.value?.data?.title || null);
useHead({
  title,
  breadcrumbs: () => templateDetailBreadcrumbs(template.value),
});

const vm = getCurrentInstance();
const toolbarRef = computed(() => (vm?.refs?.templateEditor as any)?.toolbarRef);
const hasEditPermissions = computed(() => auth.hasScope('template_editor'));
const { toolbarAttrs, fetchLoaderAttrs, readonly } = useLockEdit({
  data: template,
  fetchState,
  baseUrl,
  toolbarRef,
  hasEditPermissions,
  performSave: async (data) => {
    const res = await templateStore.update(data!);
    for (const tr of template.value!.translations) {
      if (!res.translations.some(rtr => rtr.id === tr.id)) {
        // Set server-generated ID of newly created translations
        tr.id = res.translations.find(rtr => rtr.language === tr.language)?.id || tr.id;
      }
    }
  },
  performDelete: async (data) => {
    await templateStore.delete(data!);
    await navigateTo('/templates/');
  },
  autoSaveOnUpdateData: ({ oldValue, newValue }) => {
    return oldValue!.translations.length !== newValue!.translations.length ||
      !isEqual(oldValue!.translations.map(tr => tr.language), newValue!.translations.map(tr => tr.language))
  }
});

async function uploadFile(file: File) {
  const img = await uploadFileHelper<UploadedFileInfo>(urlJoin(baseUrl.value, '/images/'), file);
  return `![](/images/name/${img.name})`;
}
function rewriteFileUrl(imgSrc: string) {
  return urlJoin(baseUrl.value, imgSrc);
}
</script>
