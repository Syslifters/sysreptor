<template>
  <component 
    :is="to ? NuxtLink : 'div'"
    :to="to || '#'"
    class="timeline-item-wrapper"
  >
    <v-timeline-item
      size="small"
      fill-dot
      :dot-color="props.value.history_type === '+' ? 'success' : props.value.history_type === '-' ? 'error' : 'info'"
      :class="{'timeline-item-link': !!to}"
      :data-testid="`timeline-item-${props.value.history_title}`"
    >
      <slot name="info">
        <chip-date :value="props.value.history_date" />
        <chip-member v-if="props.value.history_user" :value="props.value.history_user" />
        <slot name="append-infos" />
        <br>
      </slot>

      <slot name="title" >
        <span v-if="props.value.history_change_reason" :data-testid="`timeline-item-${props.value.history_title}`">{{ props.value.history_change_reason }}</span>
        <span v-else-if="props.value.history_type === '+'" :data-testid="`timeline-item-${props.value.history_title}`">Created</span>
        <span v-else-if="props.value.history_type === '-'" :data-testid="`timeline-item-${props.value.history_title}`">Deleted</span>
      </slot>
    </v-timeline-item>
  </component>
</template>

<script setup lang="ts">
import { NuxtLink } from '#components';

const props = defineProps<{
  value: HistoryTimelineRecord;
  to?: string|null;
}>();
</script>

<style lang="scss" scoped>
:deep() {
  .v-timeline-item__body, .v-timeline-divider {
    padding-block-start: 0.5em;
    padding-block-end: 0.5em;
  }

  .v-timeline-divider {
    height: 100%;
    flex-direction: column;
    grid-column: 2;
    justify-content: flex-start;
  }

  .v-timeline-item__body {
    width: 100%;
    grid-column: 3;
    justify-self: flex-start;
    padding-inline-start: 24px;
  }

  .v-timeline-divider__before {
    height: 0;
  }

  .v-timeline-divider__after {
    width: var(--v-timeline-line-thickness);
    height: calc(var(--v-timeline-line-size-base) - var(--v-timeline-dot-size) / 2 + var(--v-timeline-line-size-offset) - var(--v-timeline-line-inset));
    bottom: -12px;
  }

  .v-chip {
    cursor: inherit;
  }
}

:global(.v-timeline--truncate-line-end > .timeline-item-wrapper:last-child .v-timeline-divider__after) {
  display: none;
}

.timeline-item-link:deep(.v-timeline-item__body) {
  position: relative;
  width: 100%;
  cursor: pointer;

  &::before {
    background-color: currentColor;
    content: "";
    position: absolute;
    top: 0;
    bottom: 0;
    left: -5em;
    right: 0;
    opacity: 0;
  }

  &:hover::before {
    opacity: 0.04;
  }
}
.router-link-exact-active .timeline-item-link:deep(.v-timeline-item__body) {
  &::before {
    opacity: 0.12;
  }
}

.timeline-item-wrapper {
  display: contents;
  text-decoration: unset;
  color: unset;
}
</style>
