<template>
  <s-autocomplete 
    :value="value" @change="$emit('input', $event)"
    v-bind="autocompleteAttrs"
  >
    <template #append-item>
      <div v-if="!selectableUsers && items.hasNextPage" v-intersect="items.fetchNextPage()" />
    </template>
  </s-autocomplete>
</template>

<script>
import { CursorPaginationFetcher } from '~/utils/urls'
export default {
  props: {
    value: {
      type: [Array, Object, String],
      default: null,
    },
    label: {
      type: String,
      default: 'Pentesters',
    },
    required: {
      type: Boolean,
      default: false,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    multiple: {
      type: Boolean,
      default: false,
    },
    preventUnselectingSelf: {
      type: Boolean,
      default: false,
    },
    selectableUsers: {
      type: Array,
      default: null,
    },
    outlined: {
      type: Boolean,
      default: true,
    },
  },
  emits: ['input'],
  data() {
    return {
      items: new CursorPaginationFetcher('/pentestusers/', this.$axios, this.$toast),
      rules: {
        single: [v => !!v || 'Item is required'],
        multiple: [v => (v && v.length > 0) || 'Item is required'],
      }
    }
  },
  computed: {
    autocompleteAttrs() {
      return Object.assign({}, this.$attrs, {
        label: this.label,
        itemValue: 'id',
        itemText: u => (u.username && u.name) ? `${u.username} (${u.name})` : (u.username || u.name || ''),
        itemDisabled: u => this.preventUnselectingSelf && u.id === this.$auth.user.id && !!this.value.find(v => v.id === u.id),
        disabled: this.disabled,
        returnObject: true,
        outlined: this.outlined,
      }, 
      this.selectableUsers ? {
        items: this.selectableUsers,
      } : {
        items: this.items.data,
        loading: this.items.isLoading,
      },
      this.multiple ? {
        multiple: true,
        chips: true,
        deletableChips: true,
      } : {},
      this.required ? {
        rules: this.multiple ? this.rules.multiple : this.rules.single,
      } : {
        clearable: true
      });
    }
  }
}
</script>
