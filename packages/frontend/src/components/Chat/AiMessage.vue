<template>
  <v-expansion-panels
    v-if="props.msg.reasoning"
    flat
    class="reasoning mt-2"
  >
    <v-expansion-panel>
      <v-expansion-panel-title class="text-body-2">Reasoning...</v-expansion-panel-title>
      <v-expansion-panel-text>{{ props.msg.reasoning }}</v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
  <markdown-preview 
    v-if="props.msg.text"
    :value="props.msg.text"
    :throttle-ms="100"
  />
</template>

<script setup lang="ts">
const props = defineProps<{
  msg: ChatHistoryEntry;
}>();

</script>

<style lang="scss" scoped>
.reasoning:deep() {
  .v-expansion-panel {
    background-color: rgba(var(--v-theme-on-surface), 0.04);
  }

  .v-expansion-panel-title {
    min-height: 0 !important;
    padding: 8px;
  }

  .v-expansion-panel-text {
    white-space: pre-wrap;
    word-break: break-word;
  }
}
</style>
