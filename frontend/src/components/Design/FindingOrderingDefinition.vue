<template>
  <s-card class="mt-4 mb-4">
    <v-card-title>Finding Ordering</v-card-title>
    <v-card-text>
      <p>
        Order findings by following fields in reports:
      </p>

      <v-list density="compact" class="pa-0">
        <draggable
          :model-value="props.modelValue"
          @update:model-value="emit('update:modelValue', $event)"
          item-key="field"
          :disabled="props.disabled"
          handle=".draggable-handle"
        >
          <template #item="{element: orderConfig, index: idx}">
            <v-list-item>
              <template #prepend>
                <span v-if="idx === 0">Sort by</span>
                <span v-else>then by</span>
                <v-icon size="x-large" class="draggable-handle ml-6" :disabled="props.disabled" icon="mdi-drag" />
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
                      :disabled="props.disabled"
                      class="mt-2"
                    />
                  </v-col>
                  <v-col cols="6">
                    <s-select
                      :model-value="orderConfig.order"
                      @update:model-value="updateOrder(idx, orderConfig, $event)"
                      label="Order"
                      :items="[SortOrder.ASC, SortOrder.DESC]"
                      :disabled="props.disabled"
                      class="mt-2"
                    />
                  </v-col>
                </v-row>
              </template>

              <template #append>
                <btn-delete
                  :delete="() => deleteOrderConfig(orderConfig)"
                  :confirm="false"
                  :disabled="props.disabled"
                  button-variant="icon"
                />
              </template>
            </v-list-item>
          </template>
        </draggable>

        <v-list-item>
          <s-btn
            @click="addField"
            :disabled="props.disabled || availableFindingFields.length === 0"
            color="secondary"
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

const props = defineProps<{
  modelValue: FindingOrderingDefinition[];
  projectType: ProjectType;
  disabled?: boolean;
}>();
const emit = defineEmits<{
  'update:modelValue': [FindingOrderingDefinition[]];
}>();

const findingFields = computed(() => {
  return props.projectType.finding_field_order
    .map(f => ({ id: f, ...props.projectType.finding_fields[f] }))
    .filter(f => ![FieldDataType.LIST, FieldDataType.OBJECT, FieldDataType.USER].includes(f.type));
});
const availableFindingFields = computed(() => {
  return findingFields.value.filter(f => !props.modelValue.map(o => o.field).includes(f.id));
});

function addField() {
  emit('update:modelValue', [...props.modelValue, { field: availableFindingFields.value[0].id, order: SortOrder.ASC }]);
}
function deleteOrderConfig(orderConfig: FindingOrderingDefinition) {
  emit('update:modelValue', props.modelValue.filter(o => o !== orderConfig));
}
function updateField(idx: number, orderConfig: FindingOrderingDefinition, field: string) {
  const newOrderConfig = [...props.modelValue];
  newOrderConfig[idx] = { ...orderConfig, field };
  emit('update:modelValue', newOrderConfig);
}
function updateOrder(idx: number, orderConfig: FindingOrderingDefinition, order: SortOrder) {
  const newOrderConfig = [...props.modelValue];
  newOrderConfig[idx] = { ...orderConfig, order };
  emit('update:modelValue', newOrderConfig);
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
