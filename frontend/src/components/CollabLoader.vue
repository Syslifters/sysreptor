<template>
  <div v-if="isFirstLoad" class="centered" v-bind="$attrs">
    <v-progress-circular indeterminate size="50" />
  </div>
  <div v-else v-bind="$attrs">
    <slot />

    <v-snackbar
      v-if="!isFirstLoad"
      :model-value="connectionState !== CollabConnectionState.OPEN"
      timeout="-1"
      color="warning"
    >
      <template #text>
        <span v-if="connectionState === CollabConnectionState.CLOSED">Server connection lost</span>
        <span v-else>Connecting...</span>
      </template>
      <template #actions>
        <v-btn
          v-if="connectionState === CollabConnectionState.CLOSED"
          @click="reconnect()"
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
import { CollabConnectionState, type CollabConnectionInfo } from '~/utils/collab';

defineOptions({
  inheritAttrs: false
});

const props = defineProps<{
  collab: {
    connection: ComputedRef<CollabConnectionInfo|undefined>;
    connect: () => void;
  }
}>();
const connectionState = computed(() => props.collab.connection.value?.connectionState || CollabConnectionState.CLOSED);

const isFirstLoad = ref(true);
const reconnectAttempted = ref(0);
const warningHttpFallbackShown = ref(false);
watch(connectionState, async (newState, oldState) => {
  if (newState === CollabConnectionState.OPEN) {
    // Reset reconnect attempt counter
    reconnectAttempted.value = 0;

    // Show warning if HTTP fallback was used
    if (props.collab.connection.value?.type === CollabConnectionType.HTTP_FALLBACK && !warningHttpFallbackShown.value) {
      warningHttpFallbackShown.value = true;
      warningToast('Could not establish WebSocket connection, falling back to HTTP. Some features may be limited.');
    }
  } else if (newState === CollabConnectionState.CLOSED && !isFirstLoad.value && reconnectAttempted.value === 0) {
    await reconnect();
  }

  if (
    newState === CollabConnectionState.OPEN || 
    (newState === CollabConnectionState.CLOSED && (oldState !== undefined && oldState !== CollabConnectionState.CLOSED))
  ) {
    isFirstLoad.value = false;
  }
}, { immediate: true });

async function reconnect() {
  reconnectAttempted.value += 1;
  try {
    await nextTick();
    await props.collab.connect();
  } catch {
    if (props.collab.connection.value?.connectionError) {
      requestErrorToast(props.collab.connection.value.connectionError);
    }
  }
}
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
