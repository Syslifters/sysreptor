<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { chatConfig } from './config'
import { getChatStrings, resolveLocale } from './i18n'
import { chatHealthy, openChat } from './state'
import './styles.css'

const props = withDefaults(
  defineProps<{
    /** BCP-47 locale. Falls back to `<html lang>`. */
    locale?: string
    /** Icon URL for the button. */
    iconSrc?: string
    /**
     * CSS selector for Teleport target.
     * Default targets VitePress local search; pass another selector (or omit
     * AskAiButton) when embedding outside VitePress.
     */
    teleportTo?: string
  }>(),
  {
    locale: undefined,
    iconSrc: undefined,
    teleportTo: '.VPNavBarSearch',
  },
)

const teleportTarget = ref<HTMLElement | null>(null)

const effectiveLocale = computed(() => resolveLocale(props.locale))
const strings = computed(() => getChatStrings(effectiveLocale.value))
const label = computed(() => strings.value.askAi)
const iconSrc = computed(() => props.iconSrc || chatConfig.iconSrc)

function resolveTeleportTarget() {
  if (!props.teleportTo) {
    teleportTarget.value = null
    return
  }
  const el = document.querySelector<HTMLElement>(props.teleportTo)
  teleportTarget.value = el
}

let bodyObserver: MutationObserver | undefined

onMounted(() => {
  resolveTeleportTarget()

  bodyObserver = new MutationObserver(() => {
    if (!teleportTarget.value) resolveTeleportTarget()
  })
  bodyObserver.observe(document.body, { childList: true, subtree: true })
})

onUnmounted(() => {
  bodyObserver?.disconnect()
})

watch(
  () => props.teleportTo,
  () => resolveTeleportTarget(),
)
</script>

<template>
  <Teleport v-if="teleportTarget && chatHealthy" :to="teleportTarget">
    <button
      type="button"
      class="syslifters-ask-ai"
      :aria-label="label"
      @click="openChat"
    >
      <img class="syslifters-ask-ai-icon" :src="iconSrc" alt="" aria-hidden="true" />
      <span class="syslifters-ask-ai-label">{{ label }}</span>
    </button>
  </Teleport>
</template>
