<template>
  <split-menu v-model="menuSize">
    <template #menu>
      <report-sidebar
        :sections="sections"
        v-model:findings="findings"
        :project-type="props.projectType"
        :readonly="props.readonly"
        @create:finding="createFinding"
        v-model:selected="currentItemId"
      >
        <template #section-item-append><span /></template>
        <template #finding-item-append="{ finding }">
          <btn-delete
            :delete="() => deleteFinding(finding)"
            :disabled="props.readonly"
            button-variant="icon"
            size="small"
            density="comfortable"
          />
        </template>
      </report-sidebar>
    </template>

    <template #default>
      <template v-if="currentItemIsSection">
        <div v-for="fieldDefinition in projectType.report_sections.find(s => s.id === currentItem!.id)!.fields" :key="fieldDefinition.id">
          <dynamic-input-field
            :model-value="props.modelValue.report[fieldDefinition.id]"
            @update:model-value="updateSectionField(fieldDefinition.id, $event)"
            :id="fieldDefinition.id"
            :definition="fieldDefinition"
            v-bind="fieldAttrs"
          >
            <template #markdown-context-menu="{value, definition, disabled}">
              <btn-confirm 
                :action="() => setFieldDefinitionDefault(definition, value)"
                button-text="Save as default value"
                button-icon="mdi-content-save"
                button-variant="list-item"
                :confirm="false"
                :disabled="disabled || value === definition.default"
              />
              <btn-confirm
                :action="() => updateSectionField(fieldDefinition.id, definition.default)"
                button-text="Reset to default value"
                button-icon="mdi-undo-variant"
                button-variant="list-item"
                :confirm="false"
                :disabled="disabled || value === definition.default"
              />
            </template>
          </dynamic-input-field>
        </div>
      </template>
      <template v-else-if="currentItemIsFinding">
        <div v-for="fieldDefinition in props.projectType.finding_fields" :key="currentItem!.id + fieldDefinition.id">
          <dynamic-input-field
            :model-value="currentItem!.data[fieldDefinition.id]"
            @update:model-value="updateFindingField(fieldDefinition.id, $event)"
            :id="fieldDefinition.id"
            :definition="fieldDefinition"
            v-bind="fieldAttrs"
          >
            <template #markdown-context-menu="{value, definition, disabled}">
              <btn-confirm 
                :action="() => setFieldDefinitionDefault(definition, value)"
                button-text="Save as default value"
                button-icon="mdi-content-save"
                button-variant="list-item"
                :confirm="false"
                :disabled="disabled || value === definition.default"
              />
              <btn-confirm
                :action="() => updateFindingField(fieldDefinition.id, definition.default)"
                button-text="Reset to default value"
                button-icon="mdi-undo-variant"
                button-variant="list-item"
                :confirm="false"
                :disabled="disabled || value === definition.default"
              />
            </template>
          </dynamic-input-field>
        </div>
      </template>
    </template>
  </split-menu>
</template>

<script setup lang="ts">
import { FieldDataType, type MarkdownEditorMode, type FieldDefinition, type PentestFinding, type ReportSection } from "#imports";
import { uuidv4 } from "@base/utils/helpers";
import { omit, pick } from "lodash-es";

const props = defineProps<{
  modelValue: any;
  projectType: ProjectType;
  readonly?: boolean;
  uploadFile?: (file: File) => Promise<string>;
  rewriteFileUrlMap?: Record<string, string>;
}>();
const emit = defineEmits<{
  'update:modelValue': [any];
}>();

const localSettings = useLocalSettings();
const auth = useAuth();

const menuSize = ref(20);

const findings = computed<PentestFinding[]>({
  get: () => {
    const outerProps = ['id', 'created', 'order'];
    return (props.modelValue.findings || []).map((f: any) => ({
      ...pick(f, outerProps), 
      data: omit(f, outerProps),
    } as PentestFinding));
  },
  set: (val) => {
    emit('update:modelValue', {
      ...props.modelValue,
      findings: val.map(f => ({...omit(f, ['data']), ...f.data})),
    });
  }
});
const sections = computed(() => props.projectType.report_sections.map(s => ({
  ...s,
  data: Object.fromEntries(s.fields.map(f => [f.id, props.modelValue.report?.[f.id]])),
} as unknown as ReportSection)));

const currentItemId = ref<any|null>(null);
const currentItem = computed<ReportSection|PentestFinding|null>(() => {
  if (!currentItemId.value) {
    return null;
  }
  return sections.value.find(s => s.id === currentItemId.value) ||
    findings.value.find((f: any) => f.id === currentItemId.value) || 
    null;
})
const currentItemIsSection = computed(() => currentItemId.value && sections.value.some(s => s.id === currentItemId.value));
const currentItemIsFinding = computed(() => currentItemId.value && findings.value.some((f: any) => f.id === currentItemId.value));


function sortPreviewFindings(findings: any[]) {
  return groupFindings({
    findings: findings.map((f: any, idx: number) => ({ ...f, order: idx + 1 })),
    projectType: props.projectType,
    overrideFindingOrder: false,
    topLevelFields: true,
  }).flatMap(g => g.findings);
}
function updateSectionField(fieldId: string, value: any) {
  emit('update:modelValue', setNested(props.modelValue, 'report.' + fieldId, value));
}
function updateFindingField(fieldId: string, value: any) {
  const findingData = props.modelValue.findings.find((f: any) => f.id === currentItemId.value);
  const newFindingData = setNested(findingData, fieldId, value);
  emit('update:modelValue', {
    ...props.modelValue,
    findings: sortPreviewFindings(props.modelValue.findings.map((f: any) => f.id === currentItemId.value ? newFindingData : f)),
  });
}
function createField(definition: FieldDefinition): any {
  if (definition.type === FieldDataType.LIST) {
    return [];
  } else if (definition.type === FieldDataType.OBJECT) {
    return createObject(definition.properties!);
  }
  return definition.default;
}
function createObject(properties: FieldDefinition[]) {
  return Object.fromEntries(properties.map(d => [d.id, createField(d)]));
}
function createFinding(data?: any) {
  const findingData = createObject(props.projectType.finding_fields);
  const newFinding = {
    ...findingData,
    ...omit(data || {}, ['data']),
    ...(data?.data || {}),
    id: uuidv4(),
    created: new Date().toISOString(),
    title: findingData.title || data?.data?.title || 'New Demo Finding',
  };

  emit('update:modelValue', {
    ...props.modelValue,
    findings: (props.modelValue.findings || []).concat([newFinding]),
  });
  currentItemId.value = newFinding.id;
}
function deleteFinding(finding: any) {
  emit('update:modelValue', {
    ...props.modelValue,
    findings: props.modelValue.findings.filter((f: any) => f.id !== finding.id)
  });
  if (finding.id === currentItem.value?.id) {
    currentItemId.value = null;
  }
}
function setFieldDefinitionDefault(definition: FieldDefinition, value: any) {
  definition.default = value;
}

const fieldAttrs = computed(() => ({
  showFieldIds: true,
  uploadFile: props.uploadFile,
  rewriteFileUrlMap: props.rewriteFileUrlMap,
  selectableUsers: [auth.user.value!],
  lang: props.projectType.language,
  readonly: props.readonly,
  spellcheckEnabled: localSettings.designSpellcheckEnabled,
  'onUpdate:spellcheckEnabled': (val: boolean) => { localSettings.designSpellcheckEnabled = val },
  markdownEditorMode: localSettings.designMarkdownEditorMode,
  'onUpdate:markdownEditorMode': (val: MarkdownEditorMode) => { localSettings.designMarkdownEditorMode = val },
}));
</script>
