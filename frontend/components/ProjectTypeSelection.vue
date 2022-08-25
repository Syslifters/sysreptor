<template>
  <v-autocomplete 
    :value="value" @change="$emit('input', $event)"
    label="Design"
    :items="items.data"
    item-text="name"
    item-value="id"
    :rules="rules"
    :loading="items.isLoading"
    hide-no-data
    outlined
    class="mt-4"
  >
    <template #append-item>
      <div v-if="items.hasNextPage" v-intersect="items.fetchNextPage()" />
    </template>
  </v-autocomplete>
</template>

<script>
import { CursorPaginationFetcher } from '~/utils/urls';
export default {
  props: {
    value: {
      type: String,
      default: null,
    }
  },
  emits: ['input'],
  data() {
    return {
      items: new CursorPaginationFetcher('/projecttypes/', this.$axios, this.$toast),
      rules: [
        v => Boolean(v) || 'Item is required',
      ]
    }
  },
}
</script>
