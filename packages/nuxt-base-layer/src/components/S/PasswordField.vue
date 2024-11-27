<template>
  <div>
    <s-text-field
      v-bind="$attrs"
      :model-value="modelValue" @update:model-value="passwordChanged"
      :type="showPassword ? 'text' : 'password'"
      :label="label"
      :disabled="disabled"
      :append-inner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
      @click:append-inner="showPassword = !showPassword"
      :loading="showStrength"
      autocomplete="off"
      spellcheck="false"
      class="mt-4"
    >
      <template #loader>
        <v-progress-linear
          v-model="passwordStrengthLevel"
          :color="passwordStrengthColor"
          height="7"
        />
      </template>
    </s-text-field>
    <s-text-field
      v-if="confirm"
      ref="confirmField"
      v-model="passwordConfirmValue"
      :type="showPassword ? 'text' : 'password'"
      :label="label + ' (confirm)'"
      :disabled="disabled"
      :append-innner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
      @click:append-inner="showPassword = !showPassword"
      :rules="rules.confirmMatches"
      autocomplete="off"
      spellcheck="false"
      class="mt-6"
    />
  </div>
</template>

<script setup lang="ts">
import type { VForm } from "vuetify/lib/components/index.mjs";
import zxcvbn from 'zxcvbn';

const props = withDefaults(defineProps<{
  modelValue: string | null,
  label?: string,
  disabled?: boolean,
  confirm?: boolean,
  showStrength?: boolean,
}>(), {
  label: 'Password',
  disabled: false,
  confirm: false,
  showStrength: false,
});
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void,
}>();

const confirmField = ref<VForm|null>(null);
async function passwordChanged(val: string) {
  if (props.confirm && confirmField.value) {
    await confirmField.value.validate();
  }
  emit('update:modelValue', val);
}

const showPassword = ref(false);
const passwordConfirmValue = ref('');
const rules = {
  confirmMatches: [(p: string) => p === props.modelValue || (!p && !props.modelValue) || 'Passwords do not match'],
};

const passwordStrengthCheckResult = computed(() => zxcvbn(props.modelValue || ''));
const passwordStrengthLevel = computed(() => {
  if (!props.modelValue) {
    return 0;
  }
  return [10, 30, 50, 80, 100][passwordStrengthCheckResult.value.score];
});
const passwordStrengthColor = computed(() => {
  if (!props.modelValue) {
    return 'error';
  }
  return ['error', 'amber-darken-4', 'warning', 'lime-darken-1', 'success'][passwordStrengthCheckResult.value.score];
});
</script>
