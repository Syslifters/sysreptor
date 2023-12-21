<template>
  <v-timeline-item
    size="small"
    fill-dot
    :dot-color="props.value.history_type === '+' ? 'success' : props.value.history_type === '-' ? 'error' : 'info'"
    :class="{'timeline-item-link': !!to, 'nuxt-link-active': isExactActive}"
    @click="to ? navigate() : undefined"
    @auxclick="to ? openInNewTab($event) : undefined"
  >
    <slot name="info">
      <chip-date :value="props.value.history_date" />
      <chip-member v-if="props.value.history_user" :value="props.value.history_user" />
      <br>
    </slot>

    <slot name="title">
      <span v-if="props.value.history_change_reason">{{ props.value.history_change_reason }}</span>
      <span v-else-if="props.value.history_type === '+'">Created</span>
      <span v-else-if="props.value.history_type === '-'">Deleted</span>
    </slot>
  </v-timeline-item>
</template>

<script setup lang="ts">
const props = defineProps<{
  value: HistoryTimelineRecord;
  to?: string|null;
}>();

const { navigate, isExactActive } = useLink({
  to: props.to || '#'
});
function openInNewTab(event: MouseEvent) {
  if (event.button === 1) {
    event.preventDefault();
    window.open(props.to!, '_blank');
  }
}
</script>

<style lang="scss" scoped>
:deep() {
  .v-timeline-item__body, .v-timeline-divider {
    padding-block-start: 0.5em !important;
    padding-block-end: 0.5em !important;
  }

  .v-timeline-item__body {
    width: 100%;
  }

  .v-timeline-divider__before {
    height: 0 !important;
  }

  .v-chip {
    cursor: inherit;
  }
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
.timeline-item-link.nuxt-link-active:deep(.v-timeline-item__body) {
  &::before {
    opacity: 0.12;
  }
}
</style>
