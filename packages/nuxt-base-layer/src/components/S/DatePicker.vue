<template>
  <s-text-field
    :model-value="displayValue"
    @update:model-value="updateInputValue"
    :disabled="props.disabled"
    :readonly="props.readonly"
    :rules="rules"
    prepend-inner-icon="mdi-calendar"
    spellcheck="false"
    :clearable="!props.readonly"
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
        :disabled="props.disabled || props.readonly"
        :min="props.minDate"
        view-mode="month"
        :first-day-of-week="1"
        show-adjacent-months
        show-week
      >
        <template #append>
          <v-btn
            v-if="props.allowNever"
            @click="setNever"
            text="Never"
            prepend-icon="mdi-infinity"
            variant="text"
          />
          <v-btn
            v-else-if="isTodayAllowed"
            @click="setToday"
            text="Today"
            prepend-icon="mdi-calendar-today"
            variant="text"
          />
        </template>
      </v-date-picker>
    </v-menu>
  </s-text-field>
</template>
<script setup lang="ts">
import { formatISO, isAfter, isValid, parseISO, startOfDay } from "date-fns";

export type DatePickerValue = string|'never'|null;

const props = withDefaults(defineProps<{
  modelValue?: DatePickerValue;
  disabled?: boolean;
  readonly?: boolean;
  locale?: string;
  minDate?: string;
  allowNever?: boolean|'null-to-never';
}>(), {
  modelValue: null,
  disabled: false,
  readonly: false,
  locale: 'en',
  minDate: undefined,
  allowNever: false,
});
const emit = defineEmits<{
  'update:modelValue': [value: DatePickerValue];
  'focus': [e: FocusEvent];
  'blur': [e: FocusEvent];
}>();

const datePickerVisible = ref(false);

const displayValue = computed(() => {
  if (props.modelValue === 'never') {
    return 'Never';
  }
  return props.modelValue;
});

function updateInputValue(val: string|null) {
  if (props.allowNever && (val?.toLowerCase() === 'never')) {
    emit('update:modelValue', 'never');
    return;
  } else if (!val) {
    emit('update:modelValue', null);
    return;
  } else {
    emit('update:modelValue', val);
  }
}

const dateValue = computed({
  get: () => {
    if (!props.modelValue || props.modelValue === 'never') {
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

function setToday() {
  dateValue.value = startOfDay(new Date());
}

function setNever() {
  datePickerVisible.value = false;
  emit('update:modelValue', 'never');
}

const isTodayAllowed = computed(() => {
  if (!props.minDate) {
    return true;
  }
  const minDate = parseISO(props.minDate);
  if (!isValid(minDate)) {
    return true;
  }
  return !isAfter(startOfDay(minDate), startOfDay(new Date()));
});

const rules = [
  (d: string|null) => {
    if (!d) {
      return true;
    }
    if (props.allowNever && d.toLowerCase() === 'never') {
      return true;
    }
    if (!isValid(parseISO(d))) {
      return 'Invalid date. Expected date format: YYYY-MM-DD';
    }
    return true;
  },
]
</script>
