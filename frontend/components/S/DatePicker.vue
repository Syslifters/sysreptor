<template>
  <v-menu
    v-model="datePickerVisible"
    :disabled="disabled"
    :close-on-content-click="false"
    min-width="auto"
    offset-y
  >
    <template #activator="{ on, attrs }">
      <s-text-field
        :value="value"
        v-bind="{...$attrs, ...attrs}" v-on="{...$listeners, ...on}"
        :label="label"
        :disabled="disabled"
        prepend-inner-icon="mdi-calendar"
        readonly
        clearable 
        @click:clear="$emit('input', null)"
      />
    </template>
    <template #default>
      <v-date-picker
        :value="value"
        @input="datePickerVisible = false; $emit('input', $event);"
        :disabled="disabled"
        :locale="locale"
        :first-day-of-week="1"
      />
    </template>
  </v-menu>
</template>

<script>
export default {
  props: {
    value: {
      type: String,
      default: null,
    },
    label: {
      type: String,
      default: null,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    locale: {
      type: String,
      default: null,
    },
  },
  emits: ['input'],
  data() {
    return {
      datePickerVisible: false,
    }
  },
}
</script>
