<template>
  <div v-if="props.msg.role === MessageRole.ASSISTANT" class="assistant-message">
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
    <div
      v-if="props.isLastMessage && !props.isStreaming && props.msg.text"
      class="assistant-message-footer"
    >
      <v-divider class="w-100" />
      <div class="assistant-message-footer-actions">
        <s-btn-icon
          @click="copyToClipboard(props.msg.text || '')"
          icon="mdi-content-copy"
          class="assistant-message-copy-btn text-disabled"
          size="x-small"
          density="compact"
          v-tooltip.top="'Copy to clipboard'"
        />
      </div>
    </div>
  </div>
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
  isLastMessage?: boolean;
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

.assistant-message {
  .assistant-message-footer {
    margin-top: 0.1rem;
    margin-bottom: 0.2rem;
  }
  .assistant-message-footer-actions {
    margin-left: 0.5rem;
    margin-right: 0.5rem;
    opacity: 0;
    transition: opacity 0.15s ease;
  }
  &:hover .assistant-message-footer-actions {
    opacity: 1;
  }
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
