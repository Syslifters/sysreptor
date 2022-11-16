<template>
  <s-autocomplete 
    v-bind="$attrs"
    :value="value" @change="$emit('input', $event)"
    label="Design"
    :items="items.data"
    :item-text="pt => pt.name + (pt.source === 'imported_dependency' ? ' (imported)' : '')"
    item-value="id"
    :return-object="returnObject"
    :rules="rules"
    :loading="items.isLoading"
    :clearable="!required"
  >
    <template #append-item>
      <div v-if="items.hasNextPage" v-intersect="(e, o, isIntersecting) => isIntersecting ? items.fetchNextPage() : null" />
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
    }
  },
  emits: ['input'],
  data() {
    const items = new CursorPaginationFetcher('/projecttypes/', this.$axios, this.$toast);

    // Always add currently selected item to list
    if (this.value) {
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
