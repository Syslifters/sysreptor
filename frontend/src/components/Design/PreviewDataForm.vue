<template>
  <split-menu v-model="menuSize">
    <template #menu>
      <v-list
        v-model:selected="currentItemSelected"
        mandatory
        density="compact"
        class="pt-0"
      >
        <v-list-subheader class="mt-0">Sections</v-list-subheader>
        <v-list-item v-for="section in projectType.report_sections" :key="section.id" :value="section" link>
          <v-list-item-title class="text-body-2">{{ section.label }}</v-list-item-title>
        </v-list-item>

        <v-list-subheader>Findings</v-list-subheader>
        <v-list-item
          v-for="finding in projectType.report_preview_data.findings" :key="finding.id"
          :value="finding"
          :class="'finding-level-' + riskLevel(finding)"
          link
        >
          <v-list-item-title class="text-body-2">{{ finding.title }}</v-list-item-title>
          <template #append>
            <btn-delete
              :delete="() => deleteFinding(finding)"
              :disabled="props.disabled"
              button-variant="icon"
              size="small"
              density="comfortable"
            />
          </template>
        </v-list-item>

        <v-list-item>
          <s-btn
            @click="createFinding"
            :disabled="props.disabled"
            color="secondary"
            size="x-small"
            block
            prepend-icon="mdi-plus"
            text="Create"
          />
        </v-list-item>
      </v-list>
    </template>

    <template #default>
      <template v-if="currentItemIsSection">
        <div v-for="fieldId in currentItem.fields" :key="fieldId">
          <dynamic-input-field
            :model-value="props.modelValue.report[fieldId]"
            @update:model-value="updateSectionField(fieldId, $event)"
            :id="fieldId"
            :definition="props.projectType.report_fields[fieldId]"
            :show-field-ids="true"
            :upload-file="uploadFile"
            :rewrite-file-url="rewriteFileUrl"
            :selectable-users="[auth.user.value as UserShortInfo]"
            :lang="props.projectType.language"
            :disabled="props.disabled"
          />
        </div>
      </template>
      <template v-else-if="currentItemIsFinding">
        <div v-for="fieldId in props.projectType.finding_field_order" :key="currentItem.id + fieldId">
          <dynamic-input-field
            :model-value="currentItem[fieldId]"
            @update:model-value="updateFindingField(fieldId, $event)"
            :id="fieldId"
            :definition="props.projectType.finding_fields[fieldId]"
            :show-field-ids="true"
            :upload-file="uploadFile"
            :rewrite-file-url="rewriteFileUrl"
            :selectable-users="[auth.user.value as UserShortInfo]"
            :lang="props.projectType.language"
            :disabled="props.disabled"
          />
        </div>
      </template>
    </template>
  </split-menu>
</template>

<script setup lang="ts">
import { v4 as uuidv4 } from "uuid";
import { FieldDataType, FieldDefinitionDict, ProjectType, UserShortInfo } from "~/utils/types";
import * as cvss from "~/utils/cvss";

const props = defineProps<{
  modelValue: any;
  projectType: ProjectType;
  disabled?: boolean;
  uploadFile?: (file: File) => Promise<string>;
  rewriteFileUrl?: (fileSrc: string) => string;
}>();
const emit = defineEmits<{
  'update:modelValue': [any];
}>();

const auth = useAuth();

const menuSize = ref(20);
const currentItem = ref<any|null>(null);
const currentItemSelected = computed({
  get: () => currentItem.value ? [currentItem.value] : [],
  set: (val) => { currentItem.value = val.length > 0 ? val[0] : null; },
})
const currentItemIsSection = computed(() => {
  return currentItem.value && props.projectType.report_sections.some(s => s.id === currentItem.value.id);
});
const currentItemIsFinding = computed(() => {
  return currentItem.value && props.modelValue.findings.some((f: any) => f.id === currentItem.value.id);
});

function updateSectionField(fieldId: string, value: any) {
  emit('update:modelValue', {
    ...props.modelValue,
    report: {
      ...props.modelValue.repo,
      [fieldId]: value,
    }
  });
}
function updateFindingField(fieldId: string, value: any) {
  const newFinding = { ...currentItem.value, [fieldId]: value };
  emit('update:modelValue', {
    ...props.modelValue,
    findings: sortFindings({
      findings: props.modelValue.findings.map((f: any) => f.id === newFinding.id ? newFinding : f),
      projectType: props.projectType,
      overrideFindingOrder: false,
      topLevelFields: true,
    })
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
function createObject(properties: FieldDefinitionDict) {
  return Object.fromEntries(
    Object.entries(properties)
      .map(([k, d]) => [k, createField(d)]));
}
function createFinding() {
  const newFinding = createObject(props.projectType.finding_fields);
  newFinding.id = uuidv4();
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
}

function riskLevel(finding: any) {
  if ('severity' in props.projectType.finding_fields) {
    return cvss.levelNumberFromLevelName(finding.severity);
  } else if ('cvss' in props.projectType.finding_fields) {
    return cvss.levelNumberFromScore(cvss.scoreFromVector(finding.cvss));
  } else {
    return 'unknown';
  }
}
</script>

<style lang="scss" scoped>
@use "assets/settings" as settings;

@for $level from 1 through 5 {
  .finding-level-#{$level} {
    border-left: 0.4em solid map-get(settings.$risk-color-levels, $level);
  }
}

:deep(.v-list-subheader) {
  margin-top: 1em;
  padding-left: 0.5em !important;
}
</style>
