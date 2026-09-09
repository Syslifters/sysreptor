/**
 * Chat widget defaults. Override via `configureChat()` or component props
 * before mounting. When copying this folder elsewhere, set `apiBase` to your
 * txtai-chat (or compatible) host and point `iconSrc` at your logo.
 *
 * ALLOWED_ORIGINS on the chat service must include your page origins.
 */
export type ChatWidgetConfig = {
  apiBase: string
  /** Nav Ask AI button and chat header. */
  iconSrc: string
  /** Floating launcher button. Falls back to `iconSrc` when omitted. */
  launcherIconSrc?: string
}

export const chatConfig: ChatWidgetConfig = {
  apiBase: 'https://sysreptor-ai.external.syslifters.com',
  iconSrc: '/images/logo.svg',
  launcherIconSrc: '/images/dino-head.svg',
}

/** Merge runtime overrides into the shared config. */
export function configureChat(partial: Partial<ChatWidgetConfig>) {
  Object.assign(chatConfig, partial)
}
