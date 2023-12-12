<template>
  <s-btn-icon
    :disabled="props.disabled"
    @click="emit('click', $event)"
    size="small"
    density="comfortable"
    :variant="props.active ? 'outlined' : 'text'"
  >
    <v-badge v-if="props.dot" dot :color="props.dot">
      <v-icon size="small" :icon="props.icon" />
    </v-badge>
    <v-icon v-else size="small" :icon="props.icon" />

    <s-tooltip v-if="props.title" :text="props.title" />
  </s-btn-icon>
</template>

<script setup lang="ts">
const props = defineProps<{
  icon: string;
  title?: string;
  disabled?: boolean;
  active?: boolean;
  dot?: string;
}>();
const emit = defineEmits<{
  click: [value: MouseEvent],
}>()
</script>

<style lang="scss" scoped>
.v-btn {
  border-radius: 15%;

  &.v-btn--disabled {
    opacity: var(--v-disabled-opacity);
  }
  &:not(.v-btn--disabled) {
    pointer-events: auto;
  }
}
</style>
