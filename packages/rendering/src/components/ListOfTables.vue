<template>
  <div v-if="shouldRender">
    <slot name="default" v-bind="slotData" />
  </div>
</template>

<script setup lang="ts">
import { v4 as uuidv4 } from "uuid";
import { onMounted, ref, computed, getCurrentInstance } from "vue";
import { callForTicks, slotDataArray, getAllElements, useRenderTask } from "@/utils";

const shouldRender = ref(false);
const items = ref<any>([]);
const slotData = computed(() => slotDataArray(items.value));
const vm = getCurrentInstance();

function updateItems() {
  items.value = [];
  for (const el of getAllElements(vm, 'table caption')) {
    if (!el.id) {
      el.setAttribute('id', uuidv4());
    }
    
    const attrs = Object.fromEntries(Array.from(el.attributes).map(a => [a.name, a.value]));
    items.value.push({
      id: el.id,
      href: '#' + el.id,
      title: attrs['data-lot-title'] || el.textContent,
      attrs: attrs,
    });
  }
  shouldRender.value = true;
}
onMounted(useRenderTask(async () => {
  // Defer rendering until everything else is rendered.
  // Then look in the DOM what should be included in the TOC
  await callForTicks(3, () => updateItems());
}));
</script>
