<template>
  <v-form ref="form" class="h-100">
    <split-menu v-model="localSettings.findingFieldDefinitionMenuSize">
      <template #menu>
        <v-list
          v-model:selected="currentFieldSelection"
          :opened="['predefinedFields']"
          density="compact"
          class="pb-0 h-100 d-flex flex-column"
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
                      :delete="() => deleteField(f.id)"
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
        <div class="h-100">
          <edit-toolbar v-bind="toolbarAttrs" :form="$refs.form as VForm" />
          <template v-if="currentField === null">
            <design-finding-ordering-definition
              v-model="projectType.finding_ordering"
              :project-type="projectType"
              :readonly="readonly"
            />

            <design-input-field-definition
              v-for="f in findingFields" :key="f.id"
              :model-value="f" @update:model-value="updateField(f, $event)"
              :can-change-structure="![FieldOrigin.CORE, FieldOrigin.PREDEFINED].includes(f.origin as any)"
              :lang="projectType.language"
              :readonly="readonly"
            />
          </template>
          <design-input-field-definition
            v-else-if="currentField.type"
            :model-value="currentField" @update:model-value="updateCurrentField"
            :can-change-structure="![FieldOrigin.CORE, FieldOrigin.PREDEFINED].includes(currentField.origin as any)"
            :lang="projectType.language"
            :readonly="readonly"
          />
        </div>
      </template>
    </split-menu>
  </v-form>
</template>

<script setup lang="ts">
import omit from 'lodash/omit';
import sortBy from "lodash/sortBy";
import Draggable from "vuedraggable";
import type { VForm } from 'vuetify/components';
import { uniqueName } from '@/utils/urls';
import { useProjectTypeLockEditOptions } from "@/composables/lockedit";
import { FieldDataType, FieldOrigin } from "@/utils/types";

const localSettings = useLocalSettings();
const projectTypeStore = useProjectTypeStore();

const { data: predefinedFindingFields } = useLazyAsyncData('projecttype:predefinedFindingFields', async () => await projectTypeStore.getPredefinedFindingFields())
const { projectType, toolbarAttrs, readonly } = useProjectTypeLockEdit(await useProjectTypeLockEditOptions({
  save: true,
  saveFields: ['finding_fields', 'finding_field_order', 'finding_ordering'],
}));

const findingFields = computed({
  get: () => {
    return projectType.value.finding_field_order.map(f => ({ id: f, ...projectType.value.finding_fields[f] }));
  },
  set: (val) => {
    // Field order
    projectType.value.finding_fields = Object.fromEntries(val.map(f => [f.id, omit(f, ['id'])]));
    projectType.value.finding_field_order = val.map(f => f.id);
  }
});
const availablePredefinedFields = computed<FieldDefinitionWithId[]>(() => {
  const out = Object.entries(predefinedFindingFields.value || {})
    .map(([id, f]) => ({ id, ...f }))
    .filter(f => !findingFields.value.some(v => f.id === v.id));
  return sortBy(out, ['id']);
});

const currentField = ref<FieldDefinitionWithId|null>(null);
const allFieldsPlaceholder = { id: null } as unknown as FieldDefinitionWithId;
const currentFieldSelection = computed({
  get: () => currentField.value ? [currentField.value] : [allFieldsPlaceholder],
  set: (val) => {
    currentField.value = (val.length > 0 && val[0] !== allFieldsPlaceholder) ? val[0] : null;
  }
});

function updateField(field: FieldDefinitionWithId, val: FieldDefinitionWithId) {
  // Update field order
  const oldFieldIdx = projectType.value.finding_field_order.indexOf(field.id);
  if (oldFieldIdx !== -1) {
    projectType.value.finding_field_order[oldFieldIdx] = val.id;
  } else {
    projectType.value.finding_field_order = projectType.value.finding_field_order.filter(f => f !== field.id).concat([val.id]);
  }

  // Remove from finding ordering if data type changed to an unsupported type
  if ([FieldDataType.LIST, FieldDataType.OBJECT, FieldDataType.USER].includes(val.type)) {
    projectType.value.finding_ordering = projectType.value.finding_ordering.filter(f => f.field !== val.id);
  }

  // Update field definition
  delete projectType.value.finding_fields[field.id];
  projectType.value.finding_fields[val.id] = omit(val, ['id']);
}
function updateCurrentField(val: FieldDefinitionWithId) {
  updateField(currentField.value!, val);

  // Update current field in selection
  currentField.value = findingFields.value.find(f => f.id === val.id)!;
}
function addField() {
  const fieldId = uniqueName('new_field', projectType.value.finding_field_order);
  projectType.value.finding_fields[fieldId] = { type: FieldDataType.STRING, origin: FieldOrigin.CUSTOM, label: 'New Field', required: true, default: 'TODO: fill field in report' };
  projectType.value.finding_field_order.push(fieldId);

  currentField.value = findingFields.value.find(f => f.id === fieldId)!;
}
function addPredefinedField(event: { newIndex: number }) {
  // Predefined field is added to projectType in findingFields setter
  // Select new field as currentField
  currentField.value = findingFields.value[event.newIndex];
}
function deleteField(fieldId: string) {
  delete projectType.value.finding_fields[fieldId];
  projectType.value.finding_field_order = projectType.value.finding_field_order.filter(f => f !== fieldId);
  projectType.value.finding_ordering = projectType.value.finding_ordering.filter(f => f.field !== fieldId);
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
