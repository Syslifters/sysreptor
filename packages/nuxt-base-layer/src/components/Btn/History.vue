<template>
  <s-btn-icon
    @click="modelValue = !modelValue"
    icon="mdi-history"
    v-tooltip.bottom="'Version History'"
    data-testid="history-button"
  />
</template>

<script setup lang="ts">
const modelValue = defineModel<boolean>('modelValue');
</script>
