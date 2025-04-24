<template>
  <div>
    <s-text-field
      v-bind="$attrs"
      :model-value="modelValue" @update:model-value="passwordChanged"
      :type="showPassword ? 'text' : 'password'"
      :label="label"
      :disabled="props.disabled"
      :append-inner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
      @click:append-inner="showPassword = !showPassword"
      :loading="props.showStrength"
      :variant="props.variant"
      autocomplete="off"
      spellcheck="false"
    >
      <template #loader v-if="props.showStrength">
        <v-progress-linear
          v-model="passwordStrengthLevel"
          :color="passwordStrengthColor"
          height="7"
        />
      </template>
      <template #append v-if="props.generate">
        <s-btn 
          @click="generateNewPassword"
          icon 
          density="compact"
          :disabled="props.disabled"
        >
          <v-icon icon="mdi-lock-reset" />
          <s-tooltip activator="parent" text="Generate random password" />
        </s-btn>
      </template>
    </s-text-field>
    <s-text-field
      v-if="confirm"
      ref="confirmField"
      v-model="passwordConfirmValue"
      :type="showPassword ? 'text' : 'password'"
      :label="label + ' (confirm)'"
      :disabled="props.disabled"
      :append-innner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
      @click:append-inner="showPassword = !showPassword"
      :rules="rules.confirmMatches"
      :variant="props.variant"
      autocomplete="off"
      spellcheck="false"
      class="mt-6"
    />
  </div>
</template>

<script setup lang="ts">
import type { VTextField } from "vuetify/lib/components/index.mjs";
import zxcvbn from 'zxcvbn';

const modelValue = defineModel<string|null>();
const props = withDefaults(defineProps<{
  label?: string,
  variant?: string,
  disabled?: boolean,
  confirm?: boolean,
  showStrength?: boolean,
  generate?: boolean,
}>(), {
  label: 'Password',
  variant: undefined,
  disabled: false,
  confirm: false,
  showStrength: false,
});

const confirmField = useTemplateRef<VTextField>('confirmField');
async function passwordChanged(val: string) {
  if (props.confirm && confirmField.value) {
    await confirmField.value.validate();
  }
  modelValue.value = val;
}

const showPassword = ref(false);
const passwordConfirmValue = ref('');
const rules = {
  confirmMatches: [(p: string) => p === modelValue.value || (!p && !modelValue.value) || 'Passwords do not match'],
};

const passwordStrengthCheckResult = computed(() => zxcvbn(modelValue.value || ''));
const passwordStrengthLevel = computed(() => {
  if (!modelValue.value) {
    return 0;
  }
  return [10, 30, 50, 80, 100][passwordStrengthCheckResult.value.score];
});
const passwordStrengthColor = computed(() => {
  if (!modelValue.value) {
    return 'error';
  }
  return ['error', 'amber-darken-4', 'warning', 'lime-darken-1', 'success'][passwordStrengthCheckResult.value.score];
});

function generateNewPassword() {
  modelValue.value = generateRandomPassword()
  passwordConfirmValue.value = '';
  showPassword.value = true;
}
</script>
