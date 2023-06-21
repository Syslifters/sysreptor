<template>
  <div class="status-container ml-1 mr-1">
    <v-select 
      :value="value"
      @input="$emit('input', $event)"
      :items="items"
      label="Status"
      hide-details="auto"
      dense 
      class="mt-4"
      v-bind="$attrs"
    >
      <template #item="{item}">
        <v-list-item-icon class="mr-3">
          <v-icon :class="'status-' + item.value">{{ item.icon }}</v-icon>
        </v-list-item-icon>
        <v-list-item-content>
          <v-list-item-title>{{ item.text }}</v-list-item-title>
        </v-list-item-content>
      </template>
      <template #selection="{item}">
        <v-icon left :class="'status-' + item.value">{{ item.icon }}</v-icon> {{ item.text }}
      </template>
    </v-select>
  </div>
</template>

<script>
export const ReviewStatusItems = Object.freeze([
  { value: 'in-progress', text: 'In progress', icon: 'mdi-pencil' }, 
  { value: 'ready-for-review', text: 'Ready for review', icon: 'mdi-check' },
  { value: 'needs-improvement', text: 'Needs improvement', icon: 'mdi-exclamation-thick' },
  { value: 'finished', text: 'Finished', icon: 'mdi-check-all' }
]);

export default {
  props: {
    value: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      items: ReviewStatusItems,
    }
  }
}
</script>

<style lang="scss" scoped>
.status-container {
  width: 15em;
}

.status-finished {
  color: $status-color-finished !important;
}
</style>
