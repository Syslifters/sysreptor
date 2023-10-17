<template>
  <v-chip size="small" class="ma-1">
    <v-icon v-if="icon" size="small" start :icon="icon" />
    {{ formattedDate }}

    <s-tooltip activator="parent" :text="tooltipPrefixText + isoDate" />
  </v-chip>
</template>

<script setup lang="ts">
import { formatDistanceToNow, parseISO, formatISO9075 } from 'date-fns';

const props = withDefaults(defineProps<{
  value: string,
  icon?: string|null,
  tooltipPrefixText?: string,
  relative?: 'past' | 'future',
}>(), {
  icon: null,
  tooltipPrefixText: '',
  relative: 'past'
});

const date = computed(() => parseISO(props.value));
const isoDate = computed(() => formatISO9075(date.value));
const formattedDate = computed(() => {
  const formatted = formatDistanceToNow(date.value);
  if (props.relative === 'past') {
    return formatted + ' ago';
  } else {
    return 'in ' + formatted;
  }
});
</script>
