<template>
  <div v-if="pending" class="d-flex flex-column align-center centered" v-bind="$attrs">
    <v-progress-circular indeterminate size="50" />
  </div>
  <div v-else-if="props.fetchState.error" v-bind="$attrs">
    <v-alert color="error">
      Failed to load page: {{ props.fetchState.error?.message || props.fetchState.error }}
    </v-alert>
  </div>

  <div v-if="props.fetchState.data" v-show="!pending && !props.fetchState.error" :key="props.fetchState.data?.id" v-bind="$attrs">
    <slot />
  </div>
</template>

<script setup lang="ts">
import type { AsyncDataRequestStatus } from '#app';

defineOptions({
  inheritAttrs: false
});

const props = defineProps<{
  fetchState: {
    status: AsyncDataRequestStatus;
    error: any|null;
    data: any|null;
  };
}>();
const pending = computed(() => ['idle', 'pending'].includes(props.fetchState.status));
</script>

<style scoped>
.centered {
  margin-top: 50vh;
  transform: translateY(-50%);
}
</style>
