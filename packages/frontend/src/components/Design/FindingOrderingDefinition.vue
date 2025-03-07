<template>
  <s-card class="mt-4 mb-4">
    <v-card-title>Finding Ordering</v-card-title>
    <v-card-text>
      <p>
        Order findings by following fields in reports:
      </p>

      <v-list density="compact" class="pa-0">
        <draggable
          v-model="modelValue"
          item-key="field"
          :disabled="props.readonly"
          handle=".draggable-handle"
        >
          <template #item="{element: orderConfig, index: idx}">
            <v-list-item>
              <template #prepend>
                <span v-if="idx === 0">Sort by</span>
                <span v-else>then by</span>
                <v-icon size="x-large" class="draggable-handle ml-6" :disabled="props.readonly" icon="mdi-drag-horizontal" />
              </template>
              <template #default>
                <v-row dense>
                  <v-col cols="6">
                    <s-select
                      :model-value="orderConfig.field"
                      @update:model-value="updateField(idx, orderConfig, $event)"
                      label="Field"
                      :items="[{id: orderConfig.field}].concat(availableFindingFields)"
                      item-title="id"
                      item-value="id"
                      :readonly="props.readonly"
                      class="mt-2"
                    />
                  </v-col>
                  <v-col cols="6">
                    <s-select
                      :model-value="orderConfig.order"
                      @update:model-value="updateOrder(idx, orderConfig, $event)"
                      label="Order"
                      :items="[SortOrder.ASC, SortOrder.DESC]"
                      :readonly="props.readonly"
                      class="mt-2"
                    />
                  </v-col>
                </v-row>
              </template>

              <template #append>
                <btn-delete
                  :delete="() => deleteOrderConfig(orderConfig)"
                  :confirm="false"
                  :disabled="props.readonly"
                  button-variant="icon"
                />
              </template>
            </v-list-item>
          </template>
        </draggable>

        <v-list-item>
          <s-btn-secondary
            @click="addField"
            :disabled="props.readonly || availableFindingFields.length === 0"
            prepend-icon="mdi-plus"
            text="Add"
          />
        </v-list-item>
      </v-list>
    </v-card-text>
  </s-card>
</template>

<script setup lang="ts">
import Draggable from 'vuedraggable';
import { SortOrder, type FindingOrderingDefinition } from '#imports';

const modelValue = defineModel<FindingOrderingDefinition[]>({ required: true });
const props = defineProps<{
  projectType: ProjectType;
  readonly?: boolean;
}>();

const findingFields = computed(() => {
  return props.projectType.finding_fields
    .filter(f => ![FieldDataType.LIST, FieldDataType.OBJECT, FieldDataType.USER].includes(f.type));
});
const availableFindingFields = computed(() => {
  return findingFields.value.filter(f => !modelValue.value.map(o => o.field).includes(f.id));
});

function addField() {
  modelValue.value = [...modelValue.value, { field: availableFindingFields.value[0]!.id, order: SortOrder.ASC }];
}
function deleteOrderConfig(orderConfig: FindingOrderingDefinition) {
  modelValue.value = modelValue.value.filter(o => o !== orderConfig);
}
function updateField(idx: number, orderConfig: FindingOrderingDefinition, field: string) {
  const newOrderConfig = [...modelValue.value];
  newOrderConfig[idx] = { ...orderConfig, field };
  modelValue.value = newOrderConfig;
}
function updateOrder(idx: number, orderConfig: FindingOrderingDefinition, order: SortOrder) {
  const newOrderConfig = [...modelValue.value];
  newOrderConfig[idx] = { ...orderConfig, order };
  modelValue.value = newOrderConfig;
}
</script>

<style lang="scss" scoped>
.draggable-handle {
  cursor: grab;
}

.v-list-item:deep(.v-list-item__prepend .v-list-item__spacer) {
  width: 0.5em;
}
</style>
