<template>
  <s-tooltip>
    <template #activator="{ on }">
      <v-chip v-bind="$attrs" v-on="{...on, ...$listeners}" small class="ma-1">
        <v-icon v-if="icon" small left>{{ icon }}</v-icon>
        {{ formattedDate }}
      </v-chip>
    </template>
    <template #default>
      <span>{{ tooltipPrefixText }}{{ isoDate }}</span>
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
    icon: {
      type: String,
      default: null,
    },
    tooltipPrefixText: {
      type: String,
      default: null,
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
