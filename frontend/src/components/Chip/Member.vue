<template>
  <v-chip size="small" class="ma-1" :class="{'text-secondary': imported}">
    <template v-if="imported">
      <v-icon size="small" start class="text-secondary" icon="mdi-account-cancel" />
      {{ props.value.name }}
    </template>
    <template v-else>
      <v-icon size="small" start icon="mdi-account" />
      {{ props.value.username }}
    </template>

    <s-tooltip activator="parent" :disabled="!props.value.name">
      <span v-if="imported">{{ props.value.name }} (imported)</span>
      <span v-else>{{ props.value.name }}</span>
    </s-tooltip>
  </v-chip>
</template>

<script setup lang="ts">
import { UserShortInfo } from "~/utils/types";

const props = withDefaults(defineProps<{
  value: UserShortInfo,
  imported?: boolean,
}>(), {
  imported: false
});
</script>
