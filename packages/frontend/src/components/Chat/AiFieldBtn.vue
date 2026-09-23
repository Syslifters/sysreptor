<template>
  <s-btn-icon
    @click="prefillField"
    :disabled="props.disabled"
    icon="mdi-creation-outline"
    v-tooltip.top="'Fill with AI'"
    :style="{ opacity: props.isHovering ? 1 : 0 }"
  />
</template>

<script setup lang="ts">
const props = defineProps<{
  collabPath: string;
  disabled?: boolean;
  isHovering?: boolean|null;
}>();
const emit = defineEmits<{
  'ai-prefill': [value: { type: string; collabPath: string }];
}>();

function prefillField() {
  if (props.disabled) {
    return;
  }
  emit('ai-prefill', { type: 'fill_field', collabPath: props.collabPath });
}
</script>
