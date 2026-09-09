/**
 * Self-contained AI chat widget for Vue 3.
 *
 * Copy this entire `chat-widget/` folder into another project, install
 * `vue`, `markdown-it`, and `dompurify`, then mount `<ChatWidget />`
 * (and optionally `<AskAiButton />`) in your root layout.
 */
export { default as ChatWidget } from './ChatWidget.vue'
export { default as AskAiButton } from './AskAiButton.vue'

export { configureChat, chatConfig } from './config'
export type { ChatWidgetConfig } from './config'

export {
  chatOpen,
  chatHealthy,
  openChat,
  closeChat,
  toggleChat,
} from './state'

export {
  probeChatHealth,
  checkChatHealth,
  streamChatCompletion,
} from './api'
export type { ChatMessage, ChatStatus, StatusMeta, StreamHandlers } from './api'

export { getChatStrings, resolveLocale, isGermanLocale, statusLabel, humanizeStatus } from './i18n'
export type { ChatStrings } from './i18n'

export { renderChatMarkdown, copyText } from './markdown'
