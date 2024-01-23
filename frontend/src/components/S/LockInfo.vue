<template>
  <div v-if="props.value" class="lock-info-icon">
    <v-icon size="x-small" icon="mdi-pencil-lock" />
    <s-tooltip activator="parent">
      {{ props.value.user.username }} is editing
    </s-tooltip>
  </div>
</template>

<script setup lang="ts">
import type { LockInfo } from '@/utils/types';

const props = defineProps<{
  value?: LockInfo|null;
}>();
</script>

<style lang="scss" scoped>
.lock-info-icon {
  margin-right: 0.2em !important;
  min-width: 1em !important;
}
</style>
