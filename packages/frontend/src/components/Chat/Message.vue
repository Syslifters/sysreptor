<template>
  <template v-if="props.msg.role === MessageRole.ASSISTANT">
    <v-expansion-panels
      v-if="props.msg.reasoning"
      flat
      class="reasoning mt-2"
    >
      <v-expansion-panel>
        <v-expansion-panel-title class="text-body-medium">Reasoning...</v-expansion-panel-title>
        <v-expansion-panel-text>{{ props.msg.reasoning }}</v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
    <markdown-preview 
      v-if="props.msg.text"
      :value="props.msg.text"
      :throttle-ms="100"
    />
  </template>
  <chat-tool-call
    v-else-if="props.msg.role === MessageRole.TOOL && props.msg.tool_call"
    :value="props.msg.tool_call"
    :project="props.project"
  />
  <s-card v-else-if="props.msg.role === MessageRole.USER" variant="tonal">
    <v-card-text class="message-text">
      {{ props.msg.text }}
    </v-card-text>
  </s-card>
</template>

<script setup lang="ts">
const props = defineProps<{
  msg: ChatHistoryEntry;
  project?: PentestProject;
}>();

</script>

<style lang="scss" scoped>
.reasoning:deep() {
  .v-expansion-panel {
    background-color: color-mix(in srgb, rgb(var(--v-theme-on-surface)) 5%, transparent);
  }

  .v-expansion-panel-title {
    min-height: 0;
    padding: 8px;
  }

  .v-expansion-panel-text {
    white-space: pre-wrap;
    word-break: break-word;
  }
}
</style>
