<template>
  <span>
    <template v-for="(slot, idx) in slotNames" :key="idx">
      <slot :name="slot"></slot>
      <template v-if="idx < slotNames.length - 2">{{ props.comma }}</template>
      <template v-else-if="idx === slotNames.length - 2">{{ props.and }}</template>
    </template>
  </span>
</template>

<script setup>
import { computed, useSlots } from "vue";

const props = defineProps({
  comma: {
    type: String,
    default: ', ',
  },
  and: {
    type: String,
    default: ' and ',
  }
});

const slots = useSlots();
const slotNames = computed(() => Object.keys(slots));
</script>
