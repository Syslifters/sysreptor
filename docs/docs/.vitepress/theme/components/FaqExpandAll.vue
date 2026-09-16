<template>
  <div v-if="visible" class="faq-expand-all">
    <button type="button" class="faq-expand-all__button" @click="toggle">
      {{ expanded ? 'Collapse all' : 'Expand all' }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { onContentUpdated } from 'vitepress'
import { allFaqOpen, faqDetails, setAllFaqOpen } from '../faqFragments'

const visible = ref(false)
const expanded = ref(false)

function refresh() {
  const items = faqDetails()
  visible.value = items.length > 0
  expanded.value = allFaqOpen()
}

function toggle() {
  setAllFaqOpen(!expanded.value)
  expanded.value = allFaqOpen()
}

function onToggle() {
  expanded.value = allFaqOpen()
}

onMounted(() => {
  refresh()
  document.addEventListener('toggle', onToggle, true)
})
onUnmounted(() => {
  document.removeEventListener('toggle', onToggle, true)
})
onContentUpdated(refresh)
</script>
