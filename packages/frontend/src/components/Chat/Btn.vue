<template>
  <s-btn-icon
    v-if="apiSettings.settings!.features?.ai_agent"
    @click="toggleChatSidebar"
    icon="mdi-creation"
    v-tooltip.bottom="'AI Chat'"
  />
</template>

<script setup lang="ts">
const modelValue = defineModel<ReportingSidebarType>();
const apiSettings = useApiSettings();

function toggleChatSidebar() {
  if (modelValue.value === ReportingSidebarType.AICHAT) {
    modelValue.value = ReportingSidebarType.NONE;
  } else {
    modelValue.value = ReportingSidebarType.AICHAT;
  }
}
</script>
