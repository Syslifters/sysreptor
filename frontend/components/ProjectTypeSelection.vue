<template>
  <s-autocomplete 
    :value="value" @change="$emit('input', $event)"
    :label="label"
    :items="additionalItems.concat(items.data)"
    :item-text="formatItemText"
    item-value="id"
    :return-object="returnObject"
    :rules="rules"
    :loading="items.isLoading"
    :clearable="!required"
    v-bind="$attrs"
  >
    <template #append-item>
      <page-loader :items="items" />
    </template>
    <template #append-outer v-if="appendLink">
      <s-tooltip>
        <template #activator="{on, attrs}">
          <s-btn 
            :to="`/designs/${returnObject ? value?.id : value}/pdfdesigner/`" 
            nuxt target="_blank"
            :disabled="!value"
            icon      
            class="mr-2"
            v-bind="attrs" 
            v-on="on"
          >
            <v-icon>mdi-chevron-right-circle-outline</v-icon>
          </s-btn>
        </template>

        <template #default>Open Design</template>
      </s-tooltip>
    </template>
    <template v-for="_, name in $scopedSlots" :slot="name" slot-scope="data"><slot :name="name" v-bind="data" /></template>
  </s-autocomplete>
</template>

<script>
import { isObject } from 'lodash';
import { SearchableCursorPaginationFetcher } from '~/utils/urls';

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
    },
    queryFilters: {
      type: Object,
      default: () => ({}),
    },
    appendLink: {
      type: Boolean,
      default: false
    },
    label: {
      type: String,
      default: 'Design',
    }
  },
  emits: ['input'],
  data() {
    const items = new SearchableCursorPaginationFetcher({
      baseURL: '/projecttypes/',
      searchFilters: {
        ordering: 'name',
        scope: ['global', 'private'],
        ...this.queryFilters,
      },
      axios: this.$axios,
      toast: this.$toast,
    });

    // Always add currently selected item to list
    if (this.value && !this.additionalItems.find(i => [this.value, this.value?.id].includes(i.id))) {
      if (isObject(this.value)) {
        items.data.push(this.value);
      } else {
        this.$store.dispatch('projecttypes/getById', this.value)
          .then((t) => {
            items.data.push(t);
            if (this.returnObject) {
              this.$emit('input', t);
            }
          })
          .catch(this.$toast.requestError);
      }
    }

    return {
      items,
      rules: [
        v => !this.required || Boolean(v) || 'Item is required',
      ]
    }
  },
  methods: {
    formatItemText(pt) {
      return pt.name + ({
        imported_dependency: ' (imported)', 
        customized: ' (customized)', 
        snapshot: ` (from ${pt?.created?.split('T')?.[0]})`,
      }[pt?.source] || '') +
        (pt?.scope === 'private' ? ' (private design)' : '');
    }
  }
}
</script>
