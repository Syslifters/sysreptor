<template>
  <div class="h-100 d-flex flex-column">
    <div v-if="$slots.header" class="flex-grow-0">
      <slot name="header" />
    </div>

    <div class="flex-grow-height" :class="{'overflow-y-auto': !props.scrollbar, 'overflow-y-scroll': props.scrollbar}">
      <slot name="default" />
    </div>

    <div v-if="$slots.footer" class="flex-grow-0">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  scrollbar?: boolean
}>();
</script>
