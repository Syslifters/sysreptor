<template>
  <v-expansion-panels
    :model-value="state !== 'closed'"
    @update:model-value="userExpanded = !!$event"
    flat
    class="reasoning-panel mt-2"
  >
    <v-expansion-panel :value="true">
      <v-expansion-panel-title class="message-text text-disabled">
        <chat-thinking-placeholder v-if="props.isStreaming">
          <slot name="title">{{ titleLabel }}</slot>
        </chat-thinking-placeholder>
        <template v-else>
          <slot name="title">{{ titleLabel }}</slot>
        </template>
      </v-expansion-panel-title>
      <v-expansion-panel-text
        class="message-text text-disabled"
        :data-state="state"
      >
        <slot name="default"></slot>
      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    title?: string;
    isStreaming?: boolean;
    expandWhileStreaming?: boolean;
    maxHeightStreaming?: string;
  }>(),
  {
    title: undefined,
    isStreaming: false,
    expandWhileStreaming: false,
    maxHeightStreaming: '7em',
  },
);

const userExpanded = ref<boolean | null>(null);
const state = computed(() => {
  if (props.expandWhileStreaming && props.isStreaming && userExpanded.value === null) {
    return 'streaming';
  }
  return userExpanded.value ? 'open' : 'closed';
});

const titleLabel = computed(() => {
  if (props.title) {
    return props.title;
  }
  return props.isStreaming ? 'Thinking...' : 'Thought';
});
</script>

<style lang="scss" scoped>
.reasoning-panel:deep() {
  .v-expansion-panel {
    background-color: transparent;
  }

  .v-expansion-panel-title {
    min-height: 0;
    padding: 8px;
  }

  .v-expansion-panel-text {
    &__wrapper {
      padding-top: 0;
      padding-bottom: 0;
    }
  }
}

.v-expansion-panel-text[data-state='streaming'] {
  max-height: v-bind(maxHeightStreaming);
  overflow-y: hidden;
  display: flex;
  flex-direction: column-reverse;
  mask-image: linear-gradient(transparent, black 3em);
}
.v-expansion-panel-text[data-state='closed'] {
  max-height: 0;
  overflow: hidden;
}

.message-text {
  font-size: 0.875rem;
}
</style>
