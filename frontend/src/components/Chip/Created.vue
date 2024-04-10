<template>
  <chip-date
    :value="props.value"
    icon="mdi-file-document-plus"
    tooltip-prefix-text="Created: "
  />
</template>

<script setup lang="ts">
const props = defineProps<{
  value: string;
}>();
</script>
