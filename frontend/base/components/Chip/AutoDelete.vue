<template>
  <chip-date
    v-if="props.value"
    :value="props.value"
    icon="mdi-delete-clock"
    tooltip-prefix-text="Automatic deletion: "
    relative="future"
  />
</template>

<script setup lang="ts">
const props = defineProps< {
  value: string|null,
}>();
</script>
