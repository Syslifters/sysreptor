<template>
  <v-form ref="form" class="h-100">
    <split-menu v-model="localSettings.findingFieldDefinitionMenuSize" :content-props="{ class: 'h-100 pa-0' }">
      <template #menu>
        <v-list
          v-model:selected="currentFieldSelection"
          :opened="['predefinedFields']"
          density="compact"
          class="pt-0 pb-0 h-100 d-flex flex-column"
        >
          <div class="flex-grow-height overflow-y-auto">
            <v-list-item :value="allFieldsPlaceholder" :ripple="false" link>
              <v-list-item-title class="text-body-2">All Fields</v-list-item-title>
            </v-list-item>

            <draggable
              v-model="findingFields"
              item-key="id"
              :group="{name: 'findingFields', put: ['findingFields', 'predefinedFindingFields']}"
              @add="addPredefinedField"
              :disabled="readonly"
            >
              <template #item="{ element: f }">
                <v-list-item
                  :value="f"
                  class="draggable-item"
                  link
                  :ripple="false"
                >
                  <template #prepend>
                    <v-icon icon="mdi-drag-horizontal" />
                  </template>
                  <template #default>
                    <v-list-item-title class="text-body-2">{{ f.id }}</v-list-item-title>
                  </template>
                  <template #append>
                    <btn-delete
                      v-if="f.origin !== FieldOrigin.CORE"
                      :delete="() => deleteField(f)"
                      button-variant="icon"
                      size="small"
                      density="compact"
                      :disabled="readonly"
                    />
                  </template>
                </v-list-item>
              </template>
            </draggable>

            <v-divider />
            <v-list-group value="predefinedFields" fluid>
              <template #activator="{ props: listGroupProps }">
                <v-list-item title="Predefined Fields" v-bind="listGroupProps" />
              </template>
              <draggable
                :model-value="availablePredefinedFields"
                item-key="id"
                :sort="false"
                :group="{name: 'predefinedFindingFields'}"
              >
                <template #item="{ element: f }">
                  <v-list-item
                    class="draggable-item"
                    :ripple="false"
                  >
                    <template #prepend>
                      <v-icon icon="mdi-drag" />
                    </template>
                    <template #default>
                      <v-list-item-title class="text-body-2">{{ f.id }}</v-list-item-title>
                    </template>
                  </v-list-item>
                </template>
              </draggable>
            </v-list-group>
          </div>
          <v-divider class="mb-1" />
          <v-list-item>
            <s-btn-secondary
              @click.stop="addField"
              size="small"
              block
              :disabled="readonly"
              prepend-icon="mdi-plus"
              text="Add Custom Field"
            />
          </v-list-item>
        </v-list>
      </template>

      <template #default>
        <div class="h-100 d-flex flex-column">
          <edit-toolbar v-bind="toolbarAttrs" :form="$refs.form as VForm" />

          <v-container fluid class="pt-0 flex-grow-height overflow-y-auto">
            <template v-if="currentField === null">
              <design-finding-ordering-definition
                v-model="projectType.finding_ordering"
                :project-type="projectType"
                :readonly="readonly"
              />
              <design-finding-grouping-definition
                v-model="projectType.finding_grouping"
                :project-type="projectType"
                :readonly="readonly"
              />

              <design-input-field-definition
                v-for="f, idx in findingFields" :key="idx"
                :model-value="f" @update:model-value="updateField(f, $event)"
                :can-change-structure="![FieldOrigin.CORE, FieldOrigin.PREDEFINED].includes(f.origin as any)"
                :lang="projectType.language"
                :readonly="readonly"
                :sibling-field-ids="findingFields.filter(ff => ff !== f).map(f => f.id)"
              />
            </template>
            <design-input-field-definition
              v-else-if="currentField.type"
              :model-value="currentField" @update:model-value="updateField(currentField, $event)"
              :can-change-structure="![FieldOrigin.CORE, FieldOrigin.PREDEFINED].includes(currentField.origin as any)"
              :lang="projectType.language"
              :readonly="readonly"
              :sibling-field-ids="findingFields.filter(ff => ff !== currentField).map(f => f.id)"
            />
          </v-container>
        </div>
      </template>
    </split-menu>
  </v-form>
</template>

<script setup lang="ts">
import Draggable from "vuedraggable";
import type { VForm } from 'vuetify/components';
import { FieldDataType, FieldOrigin, type FieldDefinition, uniqueName, useProjectTypeLockEditOptions } from "#imports";

const localSettings = useLocalSettings();
const projectTypeStore = useProjectTypeStore();

const { data: predefinedFindingFields } = useLazyAsyncData('projecttype:predefinedFindingFields', async () => await projectTypeStore.getPredefinedFindingFields())
const { projectType, toolbarAttrs, readonly } = useProjectTypeLockEdit(await useProjectTypeLockEditOptions({
  save: true,
  saveFields: ['finding_fields', 'finding_ordering', 'finding_grouping'],
}));

const findingFields = computed({
  get: () => projectType.value.finding_fields,
  set: (val) => { projectType.value.finding_fields = val; }
});
const availablePredefinedFields = computed<FieldDefinition[]>(() => {
  return (predefinedFindingFields.value || [])
    .filter(f => !findingFields.value.some(v => f.id === v.id));
});

const currentField = ref<FieldDefinition|null>(null);
const allFieldsPlaceholder = { id: null } as unknown as FieldDefinition;
const currentFieldSelection = computed({
  get: () => currentField.value ? [currentField.value] : [allFieldsPlaceholder],
  set: (val) => {
    currentField.value = (val.length > 0 && val[0] !== allFieldsPlaceholder) ? val[0]! : null;
  }
});

function updateField(field: FieldDefinition, val: FieldDefinition) {
  const oldId = field.id;

  // Update field definition
  Object.keys(field).forEach(k => delete field[k as keyof FieldDefinition]);
  Object.assign(field, val);

  if ([FieldDataType.LIST, FieldDataType.OBJECT, FieldDataType.USER].includes(val.type)) {
    // Remove from finding ordering if data type changed to an unsupported type
    projectType.value.finding_ordering = projectType.value.finding_ordering.filter(o => o.field !== val.id);
    projectType.value.finding_grouping = projectType.value.finding_grouping?.filter(o => o.field !== val.id) || null;
  } else if (val.id !== oldId && projectType.value.finding_ordering.some(o => o.field === oldId)) {
    // Update references to field ID
    projectType.value.finding_ordering = projectType.value.finding_ordering.map(o => ({ ...o, field: val.id }));
    projectType.value.finding_grouping = projectType.value.finding_grouping?.map(o => ({ ...o, field: val.id })) || null;
  }
}
function addField() {
  const fieldId = uniqueName('new_field', projectType.value.finding_fields.map(f => f.id));
  const newField = { id: fieldId, type: FieldDataType.STRING, origin: FieldOrigin.CUSTOM, label: 'New Field', required: true, default: 'TODO: fill field in report' }
  projectType.value.finding_fields.push(newField);
  currentField.value = newField;
}
function addPredefinedField(event: { newIndex: number }) {
  // Predefined field is added to projectType in findingFields setter
  // Select new field as currentField
  currentField.value = findingFields.value[event.newIndex]!;
}
function deleteField(field: FieldDefinition) {
  projectType.value.finding_fields = projectType.value.finding_fields.filter(f => f !== field);
  projectType.value.finding_ordering = projectType.value.finding_ordering.filter(f => f.field !== field.id);
  if (currentField.value === field) {
    currentField.value = null;
  }
}
</script>

<style lang="scss" scoped>
.draggable-item {
  cursor: grab;
}

:deep(.v-list-item__prepend) {
  .v-list-item__spacer {
    width: 0.5em;
  }
}
</style>
