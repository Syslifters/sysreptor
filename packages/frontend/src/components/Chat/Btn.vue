<template>
  <s-btn-icon
    v-if="apiSettings.settings!.features?.ai_agent"
    @click="toggleChatSidebar"
  >
    <v-icon icon="mdi-creation" />
    <s-tooltip activator="parent" location="bottom" text="AI Chat" />
  </s-btn-icon>
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
