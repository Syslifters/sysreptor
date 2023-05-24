<template>
  <div>
    <v-text-field
      v-bind="$attrs"
      :value="value" @input="passwordChanged"
      :type="showPassword ? 'text' : 'password'"
      :label="label"
      :disabled="disabled"
      :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
      @click:append="showPassword = !showPassword"
      :loading="showStrength"
      hide-details="auto" 
      :error-count="100"
      outlined 
      autocomplete="off"
      class="mt-4"
    >
      <template #progress>
        <v-progress-linear
          :value="passwordStrengthLevel"
          :color="passwordStrengthColor"
          absolute
          height="7"
        />
      </template>
    </v-text-field>
    <v-text-field 
      v-if="confirm" ref="confirmField"
      v-model="passwordConfirmValue"
      :type="showPassword ? 'text' : 'password'"
      :label="label + ' (confirm)'"
      :disabled="disabled"
      :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
      @click:append="showPassword = !showPassword"
      :rules="rules.confirmMatches"
      hide-details="auto"
      :error-count="100"
      outlined
      autocomplete="off"
      class="mt-6"
    />
  </div>
</template>

<script>
import zxcvbn from 'zxcvbn';

export default {
  props: {
    value: {
      type: String,
      default: null,
    },
    label: {
      type: String,
      default: 'Password',
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    confirm: {
      type: Boolean,
      default: false,
    },
    showStrength: {
      type: Boolean,
      default: false,
    }
  },
  data() {
    return {
      passwordConfirmValue: null,
      showPassword: false,
      rules: {
        confirmMatches: [p => p === this.value || (!p && !this.value) || 'Passwords do not match'],
      }
    }
  },
  computed: {
    passwordStrengthCheckResult() {
      return zxcvbn(this.value || '');
    },
    passwordStrengthLevel() {
      if (!this.value) {
        return 0;
      }
      return [10, 30, 50, 80, 100][this.passwordStrengthCheckResult.score];
    },
    passwordStrengthColor() {
      if (!this.value) {
        return 'error';
      } 
      return ['error', 'amber darken-4', 'warning', 'lime darken-1', 'success'][this.passwordStrengthCheckResult.score];
    },
  },
  methods: {
    passwordChanged(val) {
      if (confirm && this.$refs.confirmField) {
        this.$refs.confirmField.validate();
      }
      this.$emit('input', val);
    }
  }
}
</script>
