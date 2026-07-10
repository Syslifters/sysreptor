<template>
  <Teleport v-if="teleportTarget && widgetVisible" :to="teleportTarget">
    <button
      type="button"
      class="sysreptor-ask-ai"
      :aria-label="label"
      @click="openWidget"
    >
      <svg
        class="sysreptor-ask-ai-icon sysreptor-ask-ai-icon-magic"
        viewBox="0 0 256 256"
        aria-hidden="true"
      >
        <path
          fill="currentColor"
          d="m 48,64 a 8,8 0 0 1 8,-8 H 72 V 40 a 8,8 0 0 1 16,0 v 16 h 16 a 8,8 0 0 1 0,16 H 88 V 88 A 8,8 0 0 1 72,88 V 72 H 56 a 8,8 0 0 1 -8,-8 z m 136,128 h -8 v -8 a 8,8 0 0 0 -16,0 v 8 h -8 a 8,8 0 0 0 0,16 h 8 v 8 a 8,8 0 0 0 16,0 v -8 h 8 a 8,8 0 0 0 0,-16 z m 56,-48 h -16 v -16 a 8,8 0 0 0 -16,0 v 16 h -16 a 8,8 0 0 0 0,16 h 16 v 16 a 8,8 0 0 0 16,0 v -16 h 16 a 8,8 0 0 0 0,-16 z M 219.31,80 80,219.31 a 16,16 0 0 1 -22.62,0 l -20.7,-20.68 a 16,16 0 0 1 0,-22.63 L 176,36.69 a 16,16 0 0 1 22.63,0 l 20.68,20.68 a 16,16 0 0 1 0,22.63 z M 164.68,112 144,91.31 48,187.31 68.68,208 Z M 208,68.69 187.31,48 l -32,32 20.69,20.69 z"
        />
      </svg>
      <img class="sysreptor-ask-ai-icon sysreptor-ask-ai-icon-logo" :src="iconSrc" alt="" aria-hidden="true" />
      <span class="sysreptor-ask-ai-label">{{ label }}</span>
    </button>
  </Teleport>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { withBase } from 'vitepress'

const WIDGET_CONTAINER_ID = 'anything-llm-embed-chat-container'
const WIDGET_OPEN_BUTTON_ID = 'anything-llm-embed-chat-button'
const NAV_SEARCH_SELECTOR = '.VPNavBarSearch'

const teleportTarget = ref<HTMLElement | null>(null)
const widgetVisible = ref(false)

const label = 'Ask AI'
const iconSrc = withBase('/images/logo.svg')

function syncWidgetVisible() {
  widgetVisible.value = document.getElementById(WIDGET_CONTAINER_ID) !== null
}

function resolveTeleportTarget() {
  const el = document.querySelector<HTMLElement>(NAV_SEARCH_SELECTOR)
  if (el) teleportTarget.value = el
}

function openWidget() {
  document.getElementById(WIDGET_OPEN_BUTTON_ID)?.click()
}

let bodyObserver: MutationObserver | undefined

onMounted(() => {
  resolveTeleportTarget()
  syncWidgetVisible()

  bodyObserver = new MutationObserver(() => {
    if (!teleportTarget.value) resolveTeleportTarget()
    syncWidgetVisible()
  })
  bodyObserver.observe(document.body, { childList: true, subtree: true })
})

onUnmounted(() => {
  bodyObserver?.disconnect()
})
</script>
