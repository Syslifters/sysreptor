<template>
  <v-chip :color="isExpired ? 'error' : undefined">
    <span v-if="!isExpired">Expires: {{ formattedDate }}</span>
    <span v-else>expired</span>

    <s-tooltip activator="parent" :text="`Expires: ${isoDate}`" />
  </v-chip>
</template>

<script setup lang="ts">
import { formatDistanceToNow, parseISO, formatISO9075, endOfDay, endOfToday } from 'date-fns';

const props = withDefaults(defineProps<{
  value?: string|null,
}>(), {
  value: null,
});

const date = computed(() => {
  if (!props.value) {
    return null;
  }
  return parseISO(props.value);
})
const isoDate = computed(() => {
  if (!date.value) {
    return 'never';
  }
  return formatISO9075(date.value, { representation: 'date' });
})
const formattedDate = computed(() => {
  if (!date.value) {
    return 'never';
  }
  return 'in ' + formatDistanceToNow(date.value);
});
const isExpired = computed(() => date.value && endOfDay(date.value) < endOfToday());
</script>
