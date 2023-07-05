<template>
  <s-tooltip>
    <template #activator="{ on }">
      <v-chip :color="isExpired ? 'error' : null" v-bind="$attrs" v-on="{...on, ...$listeners}" small class="ma-1">
        <template v-if="!isExpired">
          Expires:
          {{ formattedDate }}
        </template>
        <template v-else>
          expired
        </template>
      </v-chip>
    </template>
    <template #default>
      <span>Expires: {{ isoDate }}</span>
    </template>
  </s-tooltip>
</template>

<script>
import { formatDistanceToNow, parseISO, formatISO9075 } from 'date-fns';

export default {
  props: {
    value: {
      type: String,
      default: null,
    },
  },
  computed: {
    date() {
      if (!this.value) {
        return null;
      }
      return parseISO(this.value);
    },
    isoDate() {
      if (!this.date) {
        return 'never';
      }
      return formatISO9075(this.date, { representation: 'date' });
    },
    formattedDate() {
      if (!this.date) {
        return 'never';
      }
      return 'in ' + formatDistanceToNow(this.date);
    },
    isExpired() {
      return this.date && this.date < new Date();
    }
  }
}
</script>
