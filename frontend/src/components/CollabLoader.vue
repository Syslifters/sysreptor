<template>
  <v-snackbar
    v-if="props.collab.hasEditPermissions.value"
    :model-value="props.collab.connectionState.value !== CollabConnectionState.OPEN"
    timeout="-1"
    color="warning"
  >
    <!-- TODO: delay on initial load ? -->
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
</template>

<script setup lang="ts">
import type { CollabConnectionState } from '~/utils/collab';

const props = defineProps<{
  collab: {
    hasEditPermissions: ComputedRef<boolean>;
    connectionState: ComputedRef<CollabConnectionState>;
    connect: () => void;
  }
}>();

</script>
