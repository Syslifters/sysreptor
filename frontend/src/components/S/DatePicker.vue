<template>
  <s-text-field
    :model-value="props.modelValue"
    :disabled="props.disabled"
    prepend-inner-icon="mdi-calendar"
    readonly
    clearable
    @click:clear="emits('update:modelValue', null)"
    v-bind="$attrs"
  >
    <v-menu
      v-model="datePickerVisible"
      :disabled="props.disabled"
      :close-on-content-click="false"
      min-width="0"
      activator="parent"
    >
      <v-date-picker
        v-model="dateValue"
        v-model:input-mode="inputMode"
        :disabled="props.disabled"
        view-mode="month"
        show-adjacent-months
        show-week
      />
    </v-menu>
  </s-text-field>
</template>
<script setup lang="ts">
import { formatISO, parseISO } from "date-fns";

const props = withDefaults(defineProps<{
      modelValue?: string|null;
      disabled?: boolean;
      locale?: string;
      }>(), {
  modelValue: null,
  disabled: false,
  locale: 'en',
});
const emits = defineEmits<{
  (e: 'update:modelValue', modelValue: string|null): void,
}>();

const datePickerVisible = ref(false);
const inputMode = ref<'calendar' | 'keyboard'>('calendar');

const dateValue = computed({
  get: () => {
    if (!props.modelValue) {
      return null;
    }
    return parseISO(props.modelValue);
  },
  set: (val) => {
    if (inputMode.value === 'calendar') {
      datePickerVisible.value = false;
    }
    const formatted = val ? formatISO(val, { representation: 'date' }) : null;
    emits('update:modelValue', formatted);
  },
});
</script>
