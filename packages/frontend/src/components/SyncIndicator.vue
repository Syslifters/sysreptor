<template>
  <v-badge 
    v-if="modelValue" 
    :color="modelValue === SyncState.SAVED ? 'success' : modelValue === SyncState.DISCONNECTED ? 'error' : undefined"
    location="bottom end" 
    class="badge-save-indicator"
  >
    <template #default>
      <v-icon icon="mdi-cloud" />
    </template>
    <template #badge>
      <v-icon v-if="modelValue === SyncState.SAVED" icon="mdi-check-bold" />
      <v-icon v-else-if="modelValue == SyncState.DISCONNECTED" icon="mdi-cancel" />
      <v-icon v-else icon="mdi-sync" class="animation-rotate" />
    </template>
  </v-badge>
</template>

<script setup lang="ts">
import { SyncState } from '#imports';
const modelValue = defineModel<SyncState>();

</script>

<style lang="scss" scoped>
.badge-save-indicator:deep() {
  .v-badge__badge {
    width: 16px;
    min-width: 16px;
    height: 16px;
  }
}
.animation-rotate {
  animation: rotate 1s infinite;

  @keyframes rotate {
    from {
      transform: rotate(0);
    }
    to {
      transform: rotate(-360deg);
    }
  }
}
</style>
