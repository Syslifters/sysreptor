<template>
  <split-menu v-model="localSettings.templateInputMenuSize">
    <template #menu>
      <template-field-selector />
    </template>

    <template #default>
      <fetch-loader :fetch-state="fetchState">
        <template-editor
          v-if="template"
          v-model="template"
          :toolbar-attrs="toolbarAttrs"
          :rewrite-file-url="rewriteFileUrl"
        />

        <s-dialog v-model="saveWarningDialogVisible">
          <template #title>Remove customer data</template>
          <template #default>
            <v-card-text>
              <v-alert type="warning">
                Ensure that no customer specific data is left in the template before saving.
              </v-alert>
              <p>
                Make sure that the following data is removed and replaced with <s-code>TODO</s-code> markers:
              </p>
              <ul>
                <li>Customer specific descriptions</li>
                <li>URLs, hostnames, system identifiers</li>
                <li>Screenshots</li>
              </ul>
            </v-card-text>

            <v-card-actions>
              <v-spacer />
              <s-btn-other
                @click="saveWarningDialogVisible = false"
                text="Cancel"
              />
              <btn-confirm
                :action="() => performCreate()"
                :confirm="false"
                button-text="Save"
                button-icon="mdi-save"
                button-color="primary"
                class="ml-1"
              />
            </v-card-actions>
          </template>
        </s-dialog>
      </fetch-loader>
    </template>
  </split-menu>
</template>

<script setup lang="ts">
import { v4 as uuidv4 } from "uuid";
import urlJoin from "url-join";

const route = useRoute();
const localSettings = useLocalSettings();
const projectStore = useProjectStore();
const templateStore = useTemplateStore();

useHead({
  title: 'Templates',
  breadcrumbs: () => templateListBreadcrumbs().concat([{ title: 'New', to: route.fullPath }]),
});

if (!route.query.project || !route.query.finding) {
  throw createError('No project or finding found.');
}

const _fetchState = useLazyAsyncData(async () => {
  const [project, finding] = await Promise.all([
    projectStore.getById(route.query.project as string),
    $fetch<PentestFinding>(`/api/v1/pentestprojects/${route.query.project}/findings/${route.query.finding}/`, { method: 'GET' }),
    templateStore.getFieldDefinition(),
  ]);

  const template = {
    id: uuidv4(),
    tags: [],
    translations: [{
      id: uuidv4(),
      is_main: true,
      language: finding.language,
      status: ReviewStatus.IN_PROGRESS,
      data: Object.fromEntries(Object.entries(finding.data).filter(([key, value]) => {
        // Only copy fields that have a value and are also in the template field definition
        return value && !(Array.isArray(value) && value.length === 0) && templateStore.fieldDefinitionList.some(d => d.id === key);
      })),
    }],
  } as any as FindingTemplate;

  return {
    project,
    template,
  };
});
const fetchState = computed(() => ({
  pending: _fetchState.pending.value,
  data: _fetchState.data.value,
  error: _fetchState.error.value,
}));

const project = computed(() => fetchState.value.data?.project);
const template = computed({
  get: () => fetchState.value.data?.template || null,
  set: (val) => {
    if (val && fetchState.value.data) {
      _fetchState.data.value!.template = val;
    }
  }
});

const saveWarningDialogVisible = ref(false);
const toolbarAttrs = computed(() => ({
  save: () => { saveWarningDialogVisible.value = true; },
}));
async function performCreate() {
  const obj = await templateStore.createFromFinding(template.value!, project.value!.id);
  await navigateTo(`/templates/${obj.id}/`);
}

function rewriteFileUrl(imgSrc: string) {
  return urlJoin(`/api/v1/pentestprojects/${project.value!.id}/`, imgSrc);
}

</script>
