<template>
  <v-badge
    :model-value="pending"
    color="transparent"
    floating
    location="top end"
    :offset-x="6"
    :offset-y="12"
  >
    <v-icon icon="mdi-share-variant" />
    <template #badge>
      <v-icon icon="mdi-alert-circle" color="error" :size="21" />
    </template>
  </v-badge>
</template>

<script setup lang="ts">
defineProps<{
  pending?: boolean;
}>();
</script>
