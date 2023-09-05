<template>
  <nuxt-link :to="to" class="timeline-item-link">
    <v-timeline-item small>
      <!-- TODO: timeline styling -->
      {{ formatDatetime(value.history_date) }} <br>
      <slot name="title">
        <span v-if="value.change_reason">{{ value.change_reason }}</span>
        <span v-else-if="value.history_type === '+'">Created</span>
        <span v-else-if="value.history_type === '-'">Deleted</span>
        <span v-else-if="value.history_type === '~'">Updated</span>
      </slot>
      <template v-if="value.history_user">
        <br>
        <s-tooltip v-if="value.history_user">
          <template #activator="{on}">
            <span v-on="on">@{{ value.history_user.username }}</span>
          </template>
          <span>{{ value.history_user.name }}</span>
        </s-tooltip>
      </template>
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
      type: Object,
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
}

.timeline-item-link {
  position: relative;
  cursor: pointer;
  color: inherit;
  text-decoration: none;

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
  &:hover::before {
    opacity: 0.04;
  }
  &.nuxt-link-active::before {
    opacity: 0.12;
  }
}
</style>
