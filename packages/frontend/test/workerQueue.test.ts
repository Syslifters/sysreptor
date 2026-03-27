// @vitest-environment nuxt
import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest'
import { useWorkerQueue } from '~/composables/workerQueue'

function mockWorker() {
  const handlers: {
    message?: (e: MessageEvent) => void
    error?: (e: ErrorEvent) => void
    messageerror?: (e: Event) => void
  } = {}

  const api = {
    postMessage: vi.fn(),
    terminate: vi.fn(),
    addEventListener(type: string, fn: EventListenerOrEventListenerObject) {
      const listener = typeof fn === 'function' ? fn : (fn as EventListenerObject).handleEvent.bind(fn)
      if (type === 'message') {
        handlers.message = listener as (e: MessageEvent) => void
      }
      if (type === 'error') {
        handlers.error = listener as (e: ErrorEvent) => void
      }
      if (type === 'messageerror') {
        handlers.messageerror = listener as (e: Event) => void
      }
    },
    dispatchSuccess(messageId: string, result: unknown) {
      handlers.message?.(new MessageEvent('message', { data: { messageId, status: 'success', result } }))
    },
    dispatchError(messageId: string, error?: unknown) {
      handlers.message?.(new MessageEvent('message', { data: { messageId, status: 'error', error } }))
    },
    dispatchWorkerError(message: string) {
      handlers.error?.(new ErrorEvent('error', { message }))
    },
    dispatchMessageError() {
      handlers.messageerror?.(new Event('messageerror'))
    },
  }
  return api as Worker & typeof api
}

describe('useWorkerQueue', () => {
  let key: string

  beforeEach(() => {
    key = `workerQueueUnit:${crypto.randomUUID()}`
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  test('runs tasks in FIFO order', async () => {
    const w = mockWorker()
    w.postMessage.mockImplementation(data => {
      queueMicrotask(() => w.dispatchSuccess(data.messageId, String(data.options).toUpperCase()))
    })
    const q = useWorkerQueue<string, string>(key, () => w)
    await expect(Promise.all([q.run('a'), q.run('b')])).resolves.toEqual(['A', 'B'])
  })

  test('removes queued task on abort before it starts', async () => {
    const w = mockWorker()
    const q = useWorkerQueue<string, string>(key, () => w)
    const p1 = q.run('a')
    expect(w.postMessage).toHaveBeenCalledTimes(1)
    const firstId = (w.postMessage.mock.calls[0]![0] as { messageId: string }).messageId

    const ac = new AbortController()
    const p2 = q.run('b', { signal: ac.signal })
    expect(w.postMessage).toHaveBeenCalledTimes(1)

    ac.abort()
    await expect(p2).rejects.toMatchObject({ name: 'AbortError' })

    w.dispatchSuccess(firstId, 'done')
    await expect(p1).resolves.toBe('done')
  })

  test('aborts active task and terminates worker', async () => {
    const w = mockWorker()
    const q = useWorkerQueue<string, string>(key, () => w)
    const ac = new AbortController()
    const p = q.run('a', { signal: ac.signal })
    ac.abort()
    await expect(p).rejects.toMatchObject({ name: 'AbortError' })
    expect(w.terminate).toHaveBeenCalled()
  })

  test('rejects with timeout and terminates worker', async () => {
    vi.useFakeTimers()
    const w = mockWorker()
    const q = useWorkerQueue<string, string>(key, () => w, { timeout: 10_000 })
    const p = q.run('a')
    expect(w.postMessage).toHaveBeenCalledTimes(1)
    const assertTimeout = expect(p).rejects.toThrow('Worker timeout')
    await vi.advanceTimersByTimeAsync(10_000)
    await assertTimeout
    expect(w.terminate).toHaveBeenCalled()
  })

  test('terminates worker after idleTimeout when queue is idle', async () => {
    vi.useFakeTimers()
    const w = mockWorker()
    const q = useWorkerQueue<string, string>(key, () => w, { idleTimeout: 10_000 })
    const p = q.run('a')
    const mid = (w.postMessage.mock.calls[0]![0] as { messageId: string }).messageId
    w.dispatchSuccess(mid, 'ok')
    await expect(p).resolves.toBe('ok')
    expect(w.terminate).not.toHaveBeenCalled()

    await vi.advanceTimersByTimeAsync(10_000)
    expect(w.terminate).toHaveBeenCalled()
  })

  test('reject active task on worker error status payload', async () => {
    const w = mockWorker()
    const q = useWorkerQueue<string, string>(key, () => w)
    const p = q.run('a')
    const mid = (w.postMessage.mock.calls[0]![0] as { messageId: string }).messageId
    w.dispatchError(mid, 'bad render')
    await expect(p).rejects.toThrow('bad render')
  })

  test('reject active task on worker error event', async () => {
    const w = mockWorker()
    const q = useWorkerQueue<string, string>(key, () => w)
    const p = q.run('a')
    w.dispatchWorkerError('worker blew up')
    await expect(p).rejects.toThrow('worker blew up')
  })

  test('reject active task on messageerror', async () => {
    const w = mockWorker()
    const q = useWorkerQueue<string, string>(key, () => w)
    const p = q.run('a')
    w.dispatchMessageError()
    await expect(p).rejects.toThrow('Worker message deserialization failed')
  })

  test('terminate rejects active and queued tasks', async () => {
    const w = mockWorker()
    const q = useWorkerQueue<string, string>(key, () => w)
    const p1 = q.run('a')
    const p2 = q.run('b')
    expect(w.postMessage).toHaveBeenCalledTimes(1)
    q.terminate()
    await expect(p1).rejects.toThrow('Worker terminated')
    await expect(p2).rejects.toThrow('Worker terminated')
  })

  test('enforces maxQueueLength', async () => {
    const w = mockWorker()
    const q = useWorkerQueue<string, string>(key, () => w, { maxQueueLength: 1 })
    const p1 = q.run('a')
    const p2 = q.run('b')
    await expect(q.run('c')).rejects.toThrow('Worker queue limit reached (1)')
    const id1 = (w.postMessage.mock.calls[0]![0] as { messageId: string }).messageId
    w.dispatchSuccess(id1, 'A')
    await expect(p1).resolves.toBe('A')
    const id2 = (w.postMessage.mock.calls[1]![0] as { messageId: string }).messageId
    w.dispatchSuccess(id2, 'B')
    await expect(p2).resolves.toBe('B')
  })

  test('creates a new worker after failure and completes next run', async () => {
    const workers: ReturnType<typeof mockWorker>[] = []
    const q = useWorkerQueue<string, string>(key, () => {
      const w = mockWorker()
      workers.push(w)
      return w
    })
    const p1 = q.run('a')
    workers[0]!.dispatchWorkerError('first dead')
    await expect(p1).rejects.toThrow('first dead')

    const p2 = q.run('b')
    expect(workers.length).toBe(2)
    const w2 = workers[1]!
    const mid = (w2.postMessage.mock.calls[0]![0] as { messageId: string }).messageId
    w2.dispatchSuccess(mid, 'ok')
    await expect(p2).resolves.toBe('ok')
  })
})
