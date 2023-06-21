<template>
  <s-tooltip>
    <template #activator="{ on }">
      <v-chip v-bind="$attrs" v-on="{...on, ...$listeners}" small class="ma-1">
        <v-icon small left>mdi-file-document-plus</v-icon>
        {{ formattedDate }}
      </v-chip>
    </template>
    <template #default>
      <span>Created: {{ isoDate }}</span>
    </template>
  </s-tooltip>
</template>

<script>
import { formatDistanceToNow, parseISO, formatISO9075 } from 'date-fns';

export default {
  props: {
    value: {
      type: String,
      required: true,
    },
  },
  computed: {
    date() {
      return parseISO(this.value);
    },
    isoDate() {
      return formatISO9075(this.date);
    },
    formattedDate() {
      return formatDistanceToNow(this.date) + ' ago';
    }
  }
}
</script>
