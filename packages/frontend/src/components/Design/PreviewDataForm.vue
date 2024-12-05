<template>
  <split-menu v-model="menuSize">
    <template #menu>
      <v-list
        v-model:selected="currentItemSelected"
        mandatory
        density="compact"
        class="pb-0 pt-0 h-100 d-flex flex-column"
      >
        <div class="flex-grow-1 overflow-y-auto">
          <v-list-subheader title="Sections" class="mt-0" />
          <v-list-item v-for="section in projectType.report_sections" :key="section.id" :value="section.id" link>
            <v-list-item-title class="text-body-2">{{ section.label }}</v-list-item-title>
          </v-list-item>

          <v-list-subheader>
            <span>Findings</span>
            <s-btn-icon
              @click="createFinding"
              :disabled="props.readonly"
              icon="mdi-plus"
              size="small"
              variant="flat"
              color="secondary"
              density="compact"
              class="ml-2"
            />
          </v-list-subheader>
          <draggable
            v-model="findings"
            item-key="id"
            handle=".draggable-handle"
            :disabled="props.readonly || projectType.finding_ordering.length !== 0"
          >
            <template #item="{element: finding}">
              <v-list-item
                :value="finding.id"
                :class="'finding-level-' + riskLevel(finding)"
                :ripple="false"
                link
              >
                <template #prepend>
                  <div v-if="projectType.finding_ordering.length === 0" class="draggable-handle mr-2">
                    <v-icon :disabled="props.readonly" icon="mdi-drag-horizontal" />
                  </div>
                </template>
                <template #default>
                  <v-list-item-title class="text-body-2">{{ finding.title }}</v-list-item-title>
                </template>
                <template #append>
                  <btn-delete
                    :delete="() => deleteFinding(finding)"
                    :disabled="props.readonly"
                    button-variant="icon"
                    size="small"
                    density="comfortable"
                  />
                </template>
              </v-list-item>
            </template>
          </draggable>
        </div>

        <div>
          <v-divider class="mb-1" />
          <v-list-item>
            <s-btn-secondary
              @click="createFinding"
              :disabled="props.readonly"
              size="small"
              block
              prepend-icon="mdi-plus"
              text="Add"
            />
          </v-list-item>
        </div>
      </v-list>
    </template>

    <template #default>
      <template v-if="currentItemIsSection">
        <div v-for="fieldDefinition in currentItem.fields" :key="fieldDefinition.id">
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
        <div v-for="fieldDefinition in props.projectType.finding_fields" :key="currentItem.id + fieldDefinition.id">
          <dynamic-input-field
            :model-value="currentItem[fieldDefinition.id]"
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
import Draggable from "vuedraggable";
import { FieldDataType, type MarkdownEditorMode, type FieldDefinition } from "#imports";
import { scoreFromVector, levelNumberFromLevelName, levelNumberFromScore } from "@base/utils/cvss";
import { uuidv4 } from "@base/utils/helpers";

const props = defineProps<{
  modelValue: any;
  projectType: ProjectType;
  readonly?: boolean;
  uploadFile?: (file: File) => Promise<string>;
  rewriteFileUrl?: (fileSrc: string) => string;
}>();
const emit = defineEmits<{
  'update:modelValue': [any];
}>();

const localSettings = useLocalSettings();
const auth = useAuth();

const menuSize = ref(20);
const currentItem = ref<any|null>(null);
const currentItemSelected = computed({
  get: () => currentItem.value ? [currentItem.value.id] : [],
  set: (val) => { 
    if (val.length > 0) {
      currentItem.value = props.projectType.report_sections.find(s => s.id === val[0])
        || props.modelValue.findings.find((f: any) => f.id === val[0]);
    } else {
      currentItem.value = null;
    }
  },
})
const currentItemIsSection = computed(() => {
  return currentItem.value && props.projectType.report_sections.some(s => s.id === currentItem.value.id);
});
const currentItemIsFinding = computed(() => {
  return currentItem.value && props.modelValue.findings.some((f: any) => f.id === currentItem.value.id);
});

function sortPreviewFindings(findings: any[]) {
  return sortFindings({
    findings: findings.map((f: any, idx: number) => ({ ...f, order: idx + 1 })),
    projectType: props.projectType,
    overrideFindingOrder: false,
    topLevelFields: true,
  })
}
const findings = computed({
  get: () => sortPreviewFindings(props.modelValue.findings || []),
  set: (val) => {
    emit('update:modelValue', {
      ...props.modelValue,
      findings: sortPreviewFindings(val),
    });
  }
});

function updateSectionField(fieldId: string, value: any) {
  emit('update:modelValue', setNested(props.modelValue, 'report.' + fieldId, value));
}
function updateFindingField(fieldId: string, value: any) {
  const newFinding = setNested(currentItem.value, fieldId, value);
  emit('update:modelValue', {
    ...props.modelValue,
    findings: sortPreviewFindings(props.modelValue.findings.map((f: any) => f.id === currentItem.value.id ? newFinding : f)),
  });
  currentItem.value = newFinding;
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
function createFinding() {
  const newFinding = createObject(props.projectType.finding_fields);
  newFinding.id = uuidv4();
  newFinding.created = new Date().toISOString();
  newFinding.title = newFinding.title || 'New Demo Finding';

  emit('update:modelValue', {
    ...props.modelValue,
    findings: (props.modelValue.findings || []).concat([newFinding]),
  });
  currentItem.value = newFinding;
}
function deleteFinding(finding: any) {
  emit('update:modelValue', {
    ...props.modelValue,
    findings: props.modelValue.findings.filter((f: any) => f.id !== finding.id)
  });
  if (finding.id === currentItem.value?.id) {
    currentItem.value = null;
  }
}
function setFieldDefinitionDefault(definition: FieldDefinition, value: any) {
  definition.default = value;
}

function riskLevel(finding: any) {
  if (props.projectType.finding_fields.some(f => f.id === 'severity')) {
    return levelNumberFromLevelName(finding.severity);
  } else if (props.projectType.finding_fields.some(f => f.id === 'cvss')) {
    return levelNumberFromScore(scoreFromVector(finding.cvss));
  } else {
    return 'unknown';
  }
}

const fieldAttrs = computed(() => ({
  showFieldIds: true,
  uploadFile: props.uploadFile,
  rewriteFileUrl: props.rewriteFileUrl,
  selectableUsers: [auth.user.value!],
  lang: props.projectType.language,
  readonly: props.readonly,
  spellcheckEnabled: localSettings.designSpellcheckEnabled,
  'onUpdate:spellcheckEnabled': (val: boolean) => { localSettings.designSpellcheckEnabled = val },
  markdownEditorMode: localSettings.designMarkdownEditorMode,
  'onUpdate:markdownEditorMode': (val: MarkdownEditorMode) => { localSettings.designMarkdownEditorMode = val },
}));
</script>

<style lang="scss" scoped>
@use 'sass:map';
@use "@base/assets/settings" as settings;

@for $level from 1 through 5 {
  .finding-level-#{$level} {
    border-left: 0.4em solid map.get(settings.$risk-color-levels, $level);
  }
}

:deep(.v-list-subheader) {
  margin-top: 1em;
  padding-left: 0.5em !important;
}

.draggable-handle {
  cursor: grab;

  &:deep(.v-icon) {
    cursor: inherit;
  }
}
</style>
