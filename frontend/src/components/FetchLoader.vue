<template>
  <div v-if="props.fetchState.pending" class="d-flex flex-column align-center centered" v-bind="$attrs">
    <v-progress-circular indeterminate size="50" />
  </div>
  <div v-else-if="props.fetchState.error" v-bind="$attrs">
    <v-alert color="error">
      Failed to load page: {{ props.fetchState.error?.message || props.fetchState.error }}
    </v-alert>
  </div>

  <div v-if="props.fetchState.data" v-show="!props.fetchState.pending && !props.fetchState.error" :key="props.fetchState.data?.id" v-bind="$attrs">
    <slot />
  </div>
</template>

<script setup lang="ts">
defineOptions({
  inheritAttrs: false
});

const props = defineProps<{
  fetchState: {
    pending: boolean;
    error: any|null;
    data: any|null;
  };
}>();
</script>

<style scoped>
.centered {
  margin-top: 50vh;
  transform: translateY(-50%);
}
</style>
