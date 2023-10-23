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
      min-width="auto"
      activator="parent"
    >
      <v-date-picker
        :model-value="props.modelValue"
        @update:model-value="updateDate($event)"
        v-model:input-mode="inputMode"
        :disabled="props.disabled"
        :locale="props.locale"
        view-mode="month"
        hide-actions
        show-adjacent-months
      />
    </v-menu>
  </s-text-field>
</template>
<script setup lang="ts">
import { formatISO } from "date-fns";

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

function updateDate(val: Date) {
  if (inputMode.value === 'calendar') {
    datePickerVisible.value = false;
  }
  const formatted = val ? formatISO(val, { representation: 'date' }) : null;
  emits('update:modelValue', formatted);
}
</script>
