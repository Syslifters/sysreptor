<template>
  <s-combobox
    :value="value"
    @input="$emit('input', $event)"
    :items="tagSuggestions"
    :disabled="disabled"
    label="Tags"
    multiple
    chips deletable-chips
    :height="56"
    spellcheck="false"
    v-bind="$attrs"
    v-on="$listeners"
  >
    <template #selection="{item, parent, disabled: itemDisabled}">
      <v-chip small :disabled="itemDisabled" close @click:close="parent.selectItem(item)">
        <v-icon small left>mdi-tag</v-icon> {{ item }}
      </v-chip>
    </template>
  </s-combobox>
</template>

<script>
export default {
  props: {
    value: {
      type: Array,
      required: true,
    },
    items: {
      type: Array,
      default: () => [],
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      tagSuggestions: [...this.items, ...this.value],
    }
  },
  watch: {
    value() {
      for (const tag of this.value) {
        if (!this.tagSuggestions.includes(tag)) {
          this.tagSuggestions.push(tag);
        }
      }
    },
  },
}
</script>
