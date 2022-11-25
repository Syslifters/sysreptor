<template>
  <s-autocomplete 
    v-bind="$attrs"
    :value="value" @change="$emit('input', $event)"
    label="Design"
    :items="additionalItems.concat(items.data)"
    :item-text="pt => pt.name + (pt.source === 'imported_dependency' ? ' (imported)' : '')"
    item-value="id"
    :return-object="returnObject"
    :rules="rules"
    :loading="items.isLoading"
    :clearable="!required"
  >
    <template #append-item>
      <page-loader :items="items" />
    </template>
  </s-autocomplete>
</template>

<script>
import { isObject } from 'lodash';
import { CursorPaginationFetcher } from '~/utils/urls';

export default {
  props: {
    value: {
      type: [String, Object],
      default: null,
    },
    returnObject: {
      type: Boolean,
      default: false,
    },
    required: {
      type: Boolean,
      default: true,
    },
    additionalItems: {
      type: Array,
      default: () => ([]),
    }
  },
  emits: ['input'],
  data() {
    const items = new CursorPaginationFetcher('/projecttypes/?ordering=name', this.$axios, this.$toast);

    // Always add currently selected item to list
    if (this.value && !this.additionalItems.find(i => [this.value, this.value?.id].includes(i.id))) {
      if (isObject(this.value)) {
        items.data.push(this.value);
      } else {
        this.$axios.$get(`/projecttypes/${this.value}/`).then(t => items.data.push(t));
      }
    }

    return {
      items,
      rules: [
        v => !this.required || Boolean(v) || 'Item is required',
      ]
    }
  },
}
</script>
