<template>
  <span>
    <template v-for="(slot, idx) in slotNames" :key="idx">
      <slot :name="slot"></slot>
      <template v-if="idx < slotNames.length - 2">{{ props.comma }}</template>
      <template v-else-if="idx === slotNames.length - 2">{{ props.and }}</template>
    </template>
  </span>
</template>

<script setup lang="ts">
import { computed, useSlots } from "vue";

const props = withDefaults(defineProps<{
  comma?: string;
  and?: string;
}>(), {
  comma: ', ',
  and: ' and ',
});

defineSlots();
const slots = useSlots();
const slotNames = computed(() => Object.keys(slots));
</script>
