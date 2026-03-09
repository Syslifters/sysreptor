<template>
  <v-expansion-panels
    :model-value="state !== 'closed'"
    @update:model-value="userExpanded = !!$event"
    flat
    class="reasoning-panel mt-2"
  >
    <v-expansion-panel :value="true">
      <slot name="title">
        <v-expansion-panel-title class="message-text text-disabled">
          {{ props.title }}
        </v-expansion-panel-title>
      </slot>
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
    maxHeightStreaming?: string;
  }>(),
  {
    isStreaming: false,
    maxHeightStreaming: '7em',
  },
);

const userExpanded = ref<boolean | null>(null);
const state = computed(() => {
  if (props.isStreaming && userExpanded.value === null) {
    return 'streaming';
  }
  return userExpanded.value ? 'open' : 'closed';
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
