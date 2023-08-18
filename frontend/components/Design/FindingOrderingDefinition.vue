<template>
  <s-card class="mt-4 mb-4">
    <v-card-title>Finding Ordering</v-card-title>
    <v-card-text>
      <p class="mb-0">
        Order findings by following fields in reports:
      </p>

      <v-list>
        <draggable
          :value="value"
          @input="$emit('input', $event)"
          :disabled="disabled"
          draggable=".draggable-item"
          handle=".draggable-handle"
        >
          <v-list-item v-for="orderConfig, idx in value" :key="idx + '_' + orderConfig.field" dense class="draggable-item">
            <v-list-item-icon class="mt-6 mr-0">
              <span v-if="idx === 0">Sort by</span>
              <span v-else>then by</span>
              <v-icon left class="draggable-handle ml-6" :disabled="disabled">mdi-drag</v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-row dense>
                <v-col cols="6">
                  <s-select 
                    :value="orderConfig.field"
                    @input="updateField(idx, orderConfig, $event)"
                    label="Field"
                    :items="[{id: orderConfig.field}].concat(availableFindingFields)"
                    item-text="id"
                    item-value="id"
                    :disabled="disabled"
                  />
                </v-col>
                <v-col cols="6">
                  <s-select
                    :value="orderConfig.order"
                    @input="updateOrder(idx, orderConfig, $event)"
                    label="Order"
                    :items="['asc', 'desc']"
                    :disabled="disabled"
                  />
                </v-col>
              </v-row>
            </v-list-item-content>

            <v-list-item-action>
              <btn-delete 
                :delete="() => deleteOrderConfig(orderConfig)" 
                :confirm="false" 
                :disabled="disabled"
                icon
              />
            </v-list-item-action>
          </v-list-item>
        </draggable>

        <v-list-item>
          <s-btn
            @click="addField"
            :disabled="disabled || availableFindingFields.length === 0"
            color="secondary"
          >
            <v-icon left>mdi-plus</v-icon>
            Add
          </s-btn>
        </v-list-item>
      </v-list>
    </v-card-text>
  </s-card>
</template>

<script>
import Draggable from 'vuedraggable';

export default {
  components: { Draggable },
  props: {
    value: {
      type: Array,
      required: true,
    },
    projectType: {
      type: Object,
      required: true,
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },
  emits: ['input'],
  computed: {
    findingFields() {
      return this.projectType.finding_field_order
        .map(f => ({ id: f, ...this.projectType.finding_fields[f] }))
        .filter(f => !['list', 'object', 'user'].includes(f.type));
    },
    availableFindingFields() {
      return this.findingFields.filter(f => !this.value.map(o => o.field).includes(f.id));
    },
  },
  methods: {
    addField() {
      this.$emit('input', [...this.value, { field: this.availableFindingFields[0].id, order: 'asc' }]);
    },
    deleteOrderConfig(orderConfig) {
      this.$emit('input', this.value.filter(o => o !== orderConfig));
    },
    updateField(idx, orderConfig, field) {
      const newOrderConfig = [...this.value];
      newOrderConfig[idx] = { ...orderConfig, field };
      this.$emit('input', newOrderConfig);
    },
    updateOrder(idx, orderConfig, order) {
      const newOrderConfig = [...this.value];
      newOrderConfig[idx] = { ...orderConfig, order };
      this.$emit('input', newOrderConfig);
    },
  }
}
</script>

<style lang="scss" scoped>
.draggable-handle {
  cursor: grab;
}
</style>
