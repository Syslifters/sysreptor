<template>
  <s-btn-icon
    v-if="apiSettings.settings!.features?.ai_agent"
    @click="modelValue = !modelValue"
  >
    <v-icon icon="mdi-creation" />
    <s-tooltip activator="parent" location="bottom" text="AI Chat" />
  </s-btn-icon>
</template>

<script setup lang="ts">
const modelValue = defineModel<boolean>();
const apiSettings = useApiSettings();
</script>
