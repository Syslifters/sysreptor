<template>
  <v-chip size="small" class="ma-1">
    <v-icon v-if="icon" size="small" start :icon="icon" />
    <span v-if="props.label">{{ props.label }}:&nbsp;</span>
    {{ formattedDate }}

    <s-tooltip activator="parent" :text="(props.tooltipPrefixText || (props.label ? props.label + ': ' : '')) + isoDate" />
  </v-chip>
</template>

<script setup lang="ts">
import { formatDistanceToNow, parseISO, formatISO9075 } from 'date-fns';

const props = withDefaults(defineProps<{
  value?: string|null,
  icon?: string|null,
  label?: string|null,
  tooltipPrefixText?: string,
  relative?: 'past' | 'future',
}>(), {
  value: null,
  icon: null,
  label: null,
  tooltipPrefixText: '',
  relative: 'past'
});

const date = computed(() => props.value ? parseISO(props.value) : null);
const isoDate = computed(() => date.value ? formatISO9075(date.value) : 'never');
const formattedDate = computed(() => {
  if (!date.value) {
    return 'never';
  }

  const formatted = formatDistanceToNow(date.value);
  if (props.relative === 'past') {
    return formatted + ' ago';
  } else {
    return 'in ' + formatted;
  }
});
</script>
