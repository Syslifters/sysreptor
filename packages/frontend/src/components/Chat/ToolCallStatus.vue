<template>
  <v-icon v-if="props.status === ToolCallStatus.SUCCESS" icon="mdi-check" color="success" />
  <v-icon v-else-if="props.status === ToolCallStatus.ERROR" icon="mdi-close" color="error" />
  <s-saving-loader-spinner v-else-if="props.status === ToolCallStatus.PENDING" />
</template>

<script setup lang="ts">
import { ToolCallStatus } from '@/utils/agent';

const props = defineProps<{
  status: ToolCallStatus;
}>();
</script>
