<template>
  <s-btn-icon
    @click="emit('update:modelValue', !props.modelValue)"
  >
    <v-icon icon="mdi-history" />

    <s-tooltip activator="parent" location="bottom" text="Version History" />
  </s-btn-icon>
</template>

<script setup lang="ts">
const props = defineProps<{
  modelValue: boolean;
}>();
const emit = defineEmits<{
  'update:modelValue': [value: boolean];
}>();
</script>
