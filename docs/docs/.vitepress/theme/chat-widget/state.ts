import { ref } from 'vue'

/** Shared panel open state (nav Ask AI + floating launcher). */
export const chatOpen = ref(false)

/** True only after a successful /health probe. */
export const chatHealthy = ref(false)

export function openChat() {
  chatOpen.value = true
}

export function closeChat() {
  chatOpen.value = false
}

export function toggleChat() {
  chatOpen.value = !chatOpen.value
}
