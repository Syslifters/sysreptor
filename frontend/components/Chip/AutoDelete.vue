<template>
  <s-tooltip v-if="value">
    <template #activator="{ on }">
      <v-chip v-bind="$attrs" v-on="{...on, ...$listeners}" small class="ma-1">
        <v-icon small left>mdi-delete-clock</v-icon>
        {{ formattedDate }}
      </v-chip>
    </template>
    <template #default>
      <span>Automatic deletion: {{ isoDate }}</span>
    </template>
  </s-tooltip>
</template>

<script>
import { parseISO, formatISO, formatDistanceToNow } from 'date-fns';

export default {
  props: {
    value: {
      type: String,
      default: null,
    },
  },
  computed: {
    date() {
      return parseISO(this.value);
    },
    isoDate() {
      return formatISO(this.date, { representation: 'date' });
    },
    formattedDate() {
      return 'in ' + formatDistanceToNow(this.date);
    },
  }
}
</script>
