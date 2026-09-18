<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { probeChatHealth, streamChatCompletionWithPow, type ChatMessage, type ChatStatus } from './api'
import { chatConfig, configureChat } from './config'
import { getChatStrings, resolveLocale, statusLabel } from './i18n'
import { copyText, renderChatMarkdown } from './markdown'
import { powManager } from './pow'
import { chatHealthy, chatOpen, closeChat, openChat } from './state'
import './styles.css'

type UiMessage = ChatMessage & { id: number; status?: ChatStatus; retryAfterSec?: number }

const MAX_QUERY_LENGTH = 8000

const props = withDefaults(
  defineProps<{
    /** BCP-47 locale (e.g. `en`, `de`). Falls back to `<html lang>`. */
    locale?: string
    /** Nav / chat header icon URL. */
    iconSrc?: string
    /** Floating launcher icon URL. Falls back to `iconSrc`. */
    launcherIconSrc?: string
    /** Override chat API base URL for this mount. */
    apiBase?: string
  }>(),
  {
    locale: undefined,
    iconSrc: undefined,
    launcherIconSrc: undefined,
    apiBase: undefined,
  },
)

if (props.apiBase) configureChat({ apiBase: props.apiBase })
if (props.iconSrc) configureChat({ iconSrc: props.iconSrc })
if (props.launcherIconSrc) configureChat({ launcherIconSrc: props.launcherIconSrc })

const effectiveLocale = computed(() => resolveLocale(props.locale))
const strings = computed(() => getChatStrings(effectiveLocale.value))
const assistantIcon = computed(() => props.iconSrc || chatConfig.iconSrc)
const launcherIcon = computed(
  () => props.launcherIconSrc || chatConfig.launcherIconSrc || assistantIcon.value,
)

const expanded = ref(false)
const input = ref('')
const messages = ref<UiMessage[]>([])
const busy = ref(false)
const messagesEl = ref<HTMLElement | null>(null)
const inputEl = ref<HTMLTextAreaElement | null>(null)
let nextId = 1
let abortController: AbortController | null = null
let scrolledToReplyStart = false

onMounted(() => {
  void probeChatHealth()
})

onUnmounted(() => {
  abortController?.abort()
})

const INPUT_MAX_HEIGHT = 400

function resizeInput() {
  const el = inputEl.value
  if (!el) return
  el.style.height = 'auto'
  el.style.overflowY = 'hidden'
  const nextHeight = Math.min(el.scrollHeight, INPUT_MAX_HEIGHT)
  el.style.height = `${nextHeight}px`
  el.style.overflowY = el.scrollHeight > INPUT_MAX_HEIGHT ? 'auto' : 'hidden'
}

watch(chatOpen, async (open) => {
  if (open) {
    powManager.prepare()
    await nextTick()
    resizeInput()
    inputEl.value?.focus()
  }
})

watch(input, async () => {
  await nextTick()
  resizeInput()
})

watch(
  () => props.apiBase,
  (base) => {
    if (base) configureChat({ apiBase: base })
  },
)

watch(
  () => props.iconSrc,
  (src) => {
    if (src) configureChat({ iconSrc: src })
  },
)

watch(
  () => props.launcherIconSrc,
  (src) => {
    if (src) configureChat({ launcherIconSrc: src })
  },
)

function renderHtml(content: string) {
  return renderChatMarkdown(content)
}

function statusTextFor(msg: UiMessage) {
  if (!msg.status) return ''
  if (msg.status === 'rate_limited') {
    const n = msg.retryAfterSec ?? 0
    return strings.value.rateLimitedWait.replace('{n}', String(n))
  }
  return statusLabel(strings.value, msg.status)
}

async function flashCopied(btn: HTMLButtonElement) {
  const prev = btn.textContent
  btn.textContent = strings.value.copied
  window.setTimeout(() => {
    btn.textContent = prev
  }, 1200)
}

async function onCopyMessage(content: string, event: Event) {
  const btn = event.currentTarget as HTMLButtonElement
  if (await copyText(content)) flashCopied(btn)
}

function onMessagesClick(event: MouseEvent) {
  const target = event.target as HTMLElement | null
  const btn = target?.closest?.('button[data-copy="code"]') as HTMLButtonElement | null
  if (!btn) return
  const block = btn.closest('.sys-chat-codeblock')
  const code = block?.querySelector('code')?.textContent ?? block?.querySelector('pre')?.textContent ?? ''
  void (async () => {
    if (await copyText(code)) flashCopied(btn)
  })()
}

function scrollToReplyStart(el: HTMLElement | null) {
  if (!el || !messagesEl.value) return
  el.scrollIntoView({ block: 'start', behavior: 'smooth' })
}

async function sendMessage(text: string) {
  const trimmed = text.trim().slice(0, MAX_QUERY_LENGTH)
  if (!trimmed || busy.value) return

  input.value = ''
  const userMsg: UiMessage = { id: nextId++, role: 'user', content: trimmed }
  const assistantId = nextId++
  messages.value.push(userMsg, {
    id: assistantId,
    role: 'assistant',
    content: '',
    status: 'retrieving',
  })
  busy.value = true
  scrolledToReplyStart = false

  const assistantIndex = messages.value.length - 1

  await nextTick()
  const assistantEl = messagesEl.value?.querySelector(
    `[data-msg-id="${assistantId}"]`,
  ) as HTMLElement | null
  if (!scrolledToReplyStart) {
    scrolledToReplyStart = true
    scrollToReplyStart(assistantEl)
  }

  abortController?.abort()
  abortController = new AbortController()

  const history: ChatMessage[] = messages.value
    .filter((m) => m.id !== assistantId)
    .filter((m) => m.role === 'user' || (m.role === 'assistant' && m.content))
    .map(({ role, content }) => ({ role, content }))

  await streamChatCompletionWithPow(history, {
    signal: abortController.signal,
    onStatus: (s, meta) => {
      const msg = messages.value[assistantIndex]
      if (!msg) return
      msg.status = s ?? undefined
      msg.retryAfterSec = meta?.retryAfterSec
    },
    onContent: (chunk) => {
      const msg = messages.value[assistantIndex]
      if (!msg) return
      msg.status = undefined
      msg.retryAfterSec = undefined
      msg.content += chunk
    },
    onDone: () => {
      busy.value = false
      const msg = messages.value[assistantIndex]
      if (!msg) return
      msg.status = undefined
      msg.retryAfterSec = undefined
      if (!msg.content.trim()) {
        msg.content = strings.value.error
      }
      powManager.prepare()
    },
    onError: (err) => {
      busy.value = false
      const msg = messages.value[assistantIndex]
      if (!msg) return
      msg.status = undefined
      msg.retryAfterSec = undefined
      if (!msg.content.trim()) {
        const status = (err as Error & { status?: number }).status
        msg.content = status === 429 ? strings.value.rateLimitedError : strings.value.error
      }
    },
  }, powManager)
}

function onSubmit(event?: Event) {
  event?.preventDefault()
  void sendMessage(input.value)
}

function onSuggestion(text: string) {
  void sendMessage(text)
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    void sendMessage(input.value)
  }
}

function onExpandToggle() {
  expanded.value = !expanded.value
}

function resetChat() {
  abortController?.abort()
  abortController = null
  busy.value = false
  messages.value = []
  input.value = ''
  nextId = 1
  scrolledToReplyStart = false
  void nextTick(() => {
    resizeInput()
    inputEl.value?.focus()
  })
}
</script>

<template>
  <template v-if="chatHealthy">
    <button
      v-show="!chatOpen"
      type="button"
      class="sys-chat-launcher"
      :aria-label="strings.open"
      @click="openChat"
    >
      <img :src="launcherIcon" alt="" aria-hidden="true" />
    </button>

    <div
      v-show="chatOpen"
      class="sys-chat-root"
      :class="{ 'is-expanded': expanded }"
      role="dialog"
      aria-modal="true"
      :aria-label="strings.title"
    >
      <header class="sys-chat-header">
        <div class="sys-chat-header-brand">
          <img :src="assistantIcon" alt="" aria-hidden="true" class="sys-chat-header-logo" />
          <span class="sys-chat-header-title">{{ strings.title }}</span>
          <span class="sys-chat-header-beta">Beta</span>
        </div>
        <div class="sys-chat-header-actions">
          <button
            v-if="messages.length > 0 || busy"
            type="button"
            class="sys-chat-icon-btn"
            :aria-label="strings.reset"
            :title="strings.reset"
            @click="resetChat"
          >
            <span aria-hidden="true">↻</span>
          </button>
          <button
            type="button"
            class="sys-chat-icon-btn sys-chat-expand-btn"
            :aria-label="expanded ? strings.collapse : strings.expand"
            :title="expanded ? strings.collapse : strings.expand"
            @click="onExpandToggle"
          >
            <span aria-hidden="true">{{ expanded ? '⛶' : '⧉' }}</span>
          </button>
          <button
            type="button"
            class="sys-chat-icon-btn"
            :aria-label="strings.close"
            :title="strings.close"
            @click="closeChat"
          >
            <span aria-hidden="true">×</span>
          </button>
        </div>
      </header>

      <div ref="messagesEl" class="sys-chat-messages" @click="onMessagesClick">
        <div v-if="messages.length === 0" class="sys-chat-empty">
          <p class="sys-chat-greeting">{{ strings.greeting }}</p>
          <div class="sys-chat-suggestions">
            <button
              v-for="s in strings.suggestions"
              :key="s"
              type="button"
              class="sys-chat-suggestion"
              :disabled="busy"
              @click="onSuggestion(s)"
            >
              {{ s }}
            </button>
          </div>
        </div>

        <div
          v-for="msg in messages"
          :key="msg.id"
          class="sys-chat-msg"
          :class="`is-${msg.role}`"
          :data-msg-id="msg.id"
        >
          <div class="sys-chat-msg-body">
            <template v-if="msg.role === 'assistant'">
              <div
                v-if="msg.status && !msg.content"
                class="sys-chat-status"
                :class="`is-${msg.status}`"
                aria-live="polite"
              >
                <span class="sys-chat-status-label">{{ statusTextFor(msg) }}</span>
                <span class="sys-chat-status-dots" aria-hidden="true">
                  <span class="sys-chat-status-dot"></span>
                  <span class="sys-chat-status-dot"></span>
                  <span class="sys-chat-status-dot"></span>
                </span>
              </div>
              <div
                v-if="msg.content"
                class="sys-chat-md"
                v-html="renderHtml(msg.content)"
              />
            </template>
            <template v-else>
              <div class="sys-chat-user-text">{{ msg.content }}</div>
            </template>
          </div>
          <div v-if="msg.content" class="sys-chat-msg-actions">
            <button
              type="button"
              class="sys-chat-copy-btn"
              @click="onCopyMessage(msg.content, $event)"
            >
              {{ strings.copy }}
            </button>
          </div>
        </div>
      </div>

      <form class="sys-chat-composer" @submit="onSubmit">
        <textarea
          ref="inputEl"
          v-model="input"
          class="sys-chat-input"
          rows="1"
          :maxlength="MAX_QUERY_LENGTH"
          :placeholder="strings.placeholder"
          :disabled="busy"
          @keydown="onKeydown"
        />
        <button
          type="submit"
          class="sys-chat-send"
          :disabled="busy || !input.trim()"
          :aria-label="strings.send"
        >
          {{ strings.send }}
        </button>
      </form>

      <p class="sys-chat-disclaimer">{{ strings.disclaimer }}</p>
    </div>

    <div
      v-if="chatOpen"
      class="sys-chat-backdrop"
      aria-hidden="true"
      @click="closeChat"
    />
  </template>
</template>
