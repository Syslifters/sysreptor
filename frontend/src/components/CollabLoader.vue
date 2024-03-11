<template>
  <div v-if="isFirstLoad" class="centered" v-bind="$attrs">
    <v-progress-circular indeterminate size="50" />
  </div>
  <div v-else v-bind="$attrs">
    <slot />

    <v-snackbar
      v-if="!isFirstLoad && props.collab.hasEditPermissions.value"
      :model-value="props.collab.connectionState.value !== CollabConnectionState.OPEN"
      timeout="-1"
      color="warning"
    >
      <template #text>
        <span v-if="props.collab.connectionState.value === CollabConnectionState.CLOSED">Server connection lost</span>
        <span v-else>Connecting...</span>
      </template>
      <template #actions>
        <v-btn
          v-if="props.collab.connectionState.value === CollabConnectionState.CLOSED"
          @click="props.collab.connect()"
          variant="text"
          size="small"
          text="Try again"
        />
        <v-progress-circular v-else indeterminate size="25" />
      </template>
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { CollabConnectionState } from '~/utils/collab';

defineOptions({
  inheritAttrs: false
});

const props = defineProps<{
  collab: {
    hasEditPermissions: ComputedRef<boolean>;
    connectionState: ComputedRef<CollabConnectionState>;
    connect: () => void;
  }
}>();

const isFirstLoad = ref(true);
watch(() => props.collab.connectionState.value, (newState, oldState) => {
  if (newState === CollabConnectionState.OPEN || (newState === CollabConnectionState.CLOSED && oldState !== undefined && oldState !== CollabConnectionState.CLOSED)) {
    isFirstLoad.value = false;
  }
}, { immediate: true });
</script>

<style scoped>
.centered {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  transform: translateY(50%);
}
</style>
