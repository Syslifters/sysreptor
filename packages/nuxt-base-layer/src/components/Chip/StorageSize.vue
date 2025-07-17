<template>
  <v-chip size="small" class="ma-1">
    <v-icon size="small" start icon="mdi-database" />
    {{ props.value }}
  </v-chip>
</template>

<script setup lang="ts">
const props = defineProps<{
  value: string
}>();
</script>
