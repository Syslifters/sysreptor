import { chatConfig } from './config'
import { type PowManager, type PowSolution } from './pow'
import { chatHealthy } from './state'

const HEALTH_TIMEOUT_MS = 5000
const HEALTH_RETRY_MS = 3000
const MAX_429_RETRIES = 3
const MAX_RETRY_AFTER_MS = 60_000
const DEFAULT_RETRY_AFTER_MS = 5000

/** SSE `delta.status` value (e.g. `retrieving`, `thinking`, `searching`), or null to clear. */
export type ChatStatus = string | null

export type StatusMeta = { retryAfterSec?: number }

export type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}

export type StreamHandlers = {
  onStatus?: (status: ChatStatus, meta?: StatusMeta) => void
  onContent?: (chunk: string) => void
  onDone?: () => void
  onError?: (error: Error) => void
  signal?: AbortSignal
}

export type Fetch429RetryOptions = {
  signal?: AbortSignal
  onRetryAfter?: (secondsRemaining: number) => void
  onRetry?: () => void
  maxRetries?: number
}

/** Parse `Retry-After` as delta-seconds or HTTP-date. Returns milliseconds, or null if missing/invalid. */
export function parseRetryAfter(header: string | null | undefined): number | null {
  if (!header) return null
  const trimmed = header.trim()
  if (!trimmed) return null
  if (/^\d+$/.test(trimmed)) return Number(trimmed) * 1000
  const date = Date.parse(trimmed)
  if (Number.isNaN(date)) return null
  return Math.max(0, date - Date.now())
}

function abortError(signal?: AbortSignal): Error {
  if (signal?.reason instanceof Error) return signal.reason
  return new DOMException('Aborted', 'AbortError')
}

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(abortError(signal))
      return
    }
    const timer = window.setTimeout(() => {
      signal?.removeEventListener('abort', onAbort)
      resolve()
    }, ms)
    const onAbort = () => {
      window.clearTimeout(timer)
      reject(abortError(signal))
    }
    signal?.addEventListener('abort', onAbort, { once: true })
  })
}

async function waitWithTicks(
  ms: number,
  signal: AbortSignal | undefined,
  onTick: (secondsRemaining: number) => void,
): Promise<void> {
  const end = Date.now() + ms
  while (true) {
    if (signal?.aborted) throw abortError(signal)
    const remaining = Math.max(0, end - Date.now())
    if (remaining <= 0) return
    onTick(Math.max(1, Math.ceil(remaining / 1000)))
    await sleep(Math.min(1000, remaining), signal)
  }
}

/** Fetch, waiting on 429 Retry-After up to `maxRetries` times. Returns the last response as-is. */
export async function fetchWith429Retry(
  input: RequestInfo | URL,
  init?: RequestInit,
  opts: Fetch429RetryOptions = {},
): Promise<Response> {
  const maxRetries = opts.maxRetries ?? MAX_429_RETRIES
  const signal = opts.signal ?? init?.signal ?? undefined
  let attempt = 0

  while (true) {
    const res = await fetch(input, { ...init, signal })
    if (res.status !== 429 || attempt >= maxRetries) return res
    attempt++
    const parsed = parseRetryAfter(res.headers.get('Retry-After'))
    const backoff = DEFAULT_RETRY_AFTER_MS * 2 ** (attempt - 1)
    const waitMs = Math.min(parsed ?? backoff, MAX_RETRY_AFTER_MS)
    await waitWithTicks(waitMs, signal, (sec) => opts.onRetryAfter?.(sec))
    opts.onRetry?.()
  }
}

function retryOptsFromHandlers(handlers: StreamHandlers): Fetch429RetryOptions {
  return {
    signal: handlers.signal,
    onRetryAfter: (sec) => handlers.onStatus?.('rate_limited', { retryAfterSec: sec }),
    onRetry: () => handlers.onStatus?.('retrieving'),
  }
}

export function isPowError(status: number, detail: string): boolean {
  if (status !== 403) return false
  const lower = detail.toLowerCase()
  return lower.includes('pow') || lower.includes('proof-of-work')
}

export async function checkChatHealth(timeoutMs = HEALTH_TIMEOUT_MS): Promise<boolean> {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), timeoutMs)
  try {
    const res = await fetch(`${chatConfig.apiBase}/health`, {
      method: 'GET',
      signal: controller.signal,
    })
    if (res.status === 429) return true
    if (!res.ok) return false
    const body = (await res.json()) as { status?: string }
    return body?.status === 'ok'
  } catch {
    return false
  } finally {
    window.clearTimeout(timer)
  }
}

/** Probe health once, then retry once after a short delay on failure. */
export async function probeChatHealth(): Promise<boolean> {
  let ok = await checkChatHealth()
  if (!ok) {
    await new Promise((r) => window.setTimeout(r, HEALTH_RETRY_MS))
    ok = await checkChatHealth()
  }
  chatHealthy.value = ok
  return ok
}

function parseSseData(line: string): unknown | null {
  if (!line.startsWith('data:')) return null
  const raw = line.slice(5).trim()
  if (!raw) return null
  if (raw === '[DONE]') return '[DONE]'
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export async function streamChatCompletion(
  messages: ChatMessage[],
  handlers: StreamHandlers = {},
  pow?: PowSolution | null,
): Promise<void> {
  const { onStatus, onContent, onDone, onError, signal } = handlers

  const payload: Record<string, unknown> = {
    messages,
    stream: true,
    stream_thinking: false,
  }
  if (pow) payload.pow = pow

  let res: Response
  try {
    res = await fetchWith429Retry(
      `${chatConfig.apiBase}/v1/chat/completions`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal,
      },
      retryOptsFromHandlers(handlers),
    )
  } catch (err) {
    if (signal?.aborted) return
    onError?.(err instanceof Error ? err : new Error(String(err)))
    return
  }

  if (!res.ok || !res.body) {
    let detail = `HTTP ${res.status}`
    try {
      const errBody = await res.json()
      detail = errBody?.error?.message || errBody?.detail || detail
    } catch {
      /* ignore */
    }
    const err = new Error(detail)
    ;(err as Error & { status?: number }).status = res.status
    onError?.(err)
    return
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let sawContent = false

  /** Returns true if the stream should stop (received [DONE]). */
  const processLines = (lines: string[]): boolean => {
    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed) continue
      const data = parseSseData(trimmed)
      if (data === null) continue
      if (data === '[DONE]') {
        onStatus?.(null)
        onDone?.()
        return true
      }

      const chunk = data as {
        choices?: Array<{ delta?: { status?: string; content?: string } }>
      }
      const delta = chunk.choices?.[0]?.delta
      if (!delta) continue

      if (typeof delta.status === 'string' && delta.status.length > 0) {
        if (!sawContent) onStatus?.(delta.status)
      }

      if (typeof delta.content === 'string' && delta.content.length > 0) {
        sawContent = true
        onStatus?.(null)
        onContent?.(delta.content)
      }
    }
    return false
  }

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        buffer += decoder.decode()
        if (buffer && processLines([buffer])) return
        break
      }
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split(/\r?\n/)
      buffer = lines.pop() ?? ''
      if (processLines(lines)) return
    }
    onStatus?.(null)
    onDone?.()
  } catch (err) {
    if (signal?.aborted) return
    onError?.(err instanceof Error ? err : new Error(String(err)))
  }
}

export async function streamChatCompletionWithPow(
  messages: ChatMessage[],
  handlers: StreamHandlers = {},
  manager: PowManager,
): Promise<void> {
  const retryOpts = retryOptsFromHandlers(handlers)
  let retried = false

  const attempt = async (pow: PowSolution | null): Promise<void> => {
    let failed = false

    await streamChatCompletion(messages, {
      ...handlers,
      onError: (err) => {
        const status = (err as Error & { status?: number }).status
        if (!retried && status != null && isPowError(status, err.message)) {
          failed = true
          return
        }
        handlers.onError?.(err)
      },
    }, pow)

    if (!failed) return

    retried = true
    const fresh = await manager.fetchAndSolve(retryOpts)
    await streamChatCompletion(messages, handlers, fresh)
  }

  try {
    const pow = await manager.consumeReady(retryOpts)
    await attempt(pow)
  } catch (err) {
    if (handlers.signal?.aborted) return
    handlers.onError?.(err instanceof Error ? err : new Error(String(err)))
  }
}
