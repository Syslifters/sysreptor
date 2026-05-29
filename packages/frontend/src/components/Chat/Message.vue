<template>
  <template v-if="props.msg.role === MessageRole.ASSISTANT">
    <chat-reasoning-panel
      v-if="props.msg.reasoning"
      title="Reasoning..."
      :is-streaming="props.isStreaming && !props.msg.text"
    >
      <template #default>
        <div class="reasoning-content message-text">
          {{ props.msg.reasoning }}
        </div>
      </template>
    </chat-reasoning-panel>
    <markdown-preview 
      v-if="props.msg.text"
      :value="props.msg.text"
      :throttle-ms="100"
      :readonly="true"
      class="message-text"
    />
  </template>
  <chat-tool-call
    v-else-if="props.msg.role === MessageRole.TOOL && props.msg.tool_call"
    :value="props.msg.tool_call"
    :project="props.project"
    :is-streaming="props.isStreaming"
  />
  <s-card
    v-else-if="props.msg.role === MessageRole.USER"
    variant="tonal"
    class="user-message"
  >
    <s-btn-icon
      @click="copyToClipboard(props.msg.text || '')"
      icon="mdi-content-copy"
      class="user-message-copy-btn"
      size="small"
      density="compact"
      v-tooltip.top="'Copy to clipboard'"
    />
    <v-card-text class="message-text">
      {{ props.msg.text }}
    </v-card-text>
  </s-card>
</template>

<script setup lang="ts">
const props = defineProps<{
  msg: ChatHistoryEntry;
  project?: PentestProject;
  isStreaming?: boolean;
}>();
</script>

<style lang="scss" scoped>
.reasoning-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.message-text {
  font-size: 0.875rem;
}

.user-message {
  position: relative;

  .user-message-copy-btn {
    position: absolute;
    top: 0.25rem;
    right: 0.25rem;
    width: 2rem;
    height: 2rem;

    border-radius: 4px;
    z-index: 1;
    opacity: 0;
    transition: opacity 0.15s ease;
  }
  &:hover .user-message-copy-btn {
    opacity: 1;
  }
}
</style>
