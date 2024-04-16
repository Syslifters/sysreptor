<template>
  <s-text-field
    :model-value="props.modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    :disabled="props.disabled"
    :readonly="props.readonly"
    :rules="rules"
    prepend-inner-icon="mdi-calendar"
    spellcheck="false"
    :clearable="props.readonly"
    @click:clear="emit('update:modelValue', null)"
    @focus="emit('focus', $event)"
    @blur="emit('blur', $event)"
    v-bind="$attrs"
  >
    <template #label v-if="$slots.label"><slot name="label" /></template>

    <v-menu
      v-model="datePickerVisible"
      :disabled="props.disabled || props.readonly"
      :close-on-content-click="false"
      min-width="0"
      activator="parent"
    >
      <v-date-picker
        v-model="dateValue"
        :disabled="props.disabled || props.disabled"
        :min="props.minDate"
        view-mode="month"
        show-adjacent-months
        show-week
      />
    </v-menu>
  </s-text-field>
</template>
<script setup lang="ts">
import { formatISO, isValid, parseISO } from "date-fns";

const props = withDefaults(defineProps<{
  modelValue?: string|null;
  disabled?: boolean;
  readonly?: boolean;
  locale?: string;
  minDate?: string;
}>(), {
  modelValue: null,
  disabled: false,
  readonly: false,
  locale: 'en',
  minDate: undefined,
});
const emit = defineEmits<{
  'update:modelValue': [value: string|null];
  'focus': [e: FocusEvent];
  'blur': [e: FocusEvent];
}>();

const datePickerVisible = ref(false);

const dateValue = computed({
  get: () => {
    if (!props.modelValue) {
      return null;
    }
    const date = parseISO(props.modelValue);
    if (!isValid(date)) {
      return null;
    }
    return date;
  },
  set: (val) => {
    datePickerVisible.value = false;
    const formatted = val ? formatISO(val, { representation: 'date' }) : null;
    emit('update:modelValue', formatted);
  },
});

const rules = [
  (d: string|null) => {
    if (!d) {
      return true;
    }
    if (!isValid(parseISO(d))) {
      return 'Invalid date. Expected date format: YYYY-MM-DD';
    }
    return true;
  },
]
</script>
