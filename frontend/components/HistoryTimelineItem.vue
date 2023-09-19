<template>
  <nuxt-link :to="to || '#'" exact :disabled="!to" :class="{'timeline-item-link': true, 'disabled': !to}">
    <v-timeline-item small fill-dot :color="value.history_type === '+' ? 'success' : value.history_type === '-' ? 'error' : 'primary'">
      <slot name="info">
        <chip-date :value="value.history_date" />
        <chip-member v-if="value.history_user" :value="value.history_user" />
        <br>
      </slot>

      <slot name="title">
        <span v-if="value.history_change_reason">{{ value.history_change_reason }}</span>
        <span v-else-if="value.history_type === '+'">Created</span>
        <span v-else-if="value.history_type === '-'">Deleted</span>
      </slot>
    </v-timeline-item>
  </nuxt-link>
</template>

<script>
import { formatISO9075 } from 'date-fns';

export default {
  props: {
    value: {
      type: Object,
      required: true,
    },
    to: {
      type: [Object, String],
      default: null,
    },
  },
  methods: {
    formatDatetime(datetime) {
      return formatISO9075(new Date(datetime));
    },
  }
}
</script>

<style lang="scss" scoped>
.v-timeline-item {
  padding-top: 0.5em;
  padding-bottom: 0.5em;

  &:deep(.v-chip) {
    cursor: inherit;
  }
}

.timeline-item-link {
  position: relative;
  color: inherit;
  text-decoration: none;
  cursor: default;

  &::before {
    background-color: currentColor;
    content: "";
    position: absolute;
    top: 0;
    bottom: 0;
    left: 0;
    right: 0;
    opacity: 0;
  }

  &:not(.disabled) {
    cursor: pointer;

    &:hover::before {
      opacity: 0.04;
    }
    &.nuxt-link-active::before {
      opacity: 0.12;
    }
  }
}
</style>
