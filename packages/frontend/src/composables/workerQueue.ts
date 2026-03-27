type QueueTask<TRequest, TResponse> = {
  messageId: string;
  request: TRequest;
  timeout?: number;
  signal?: AbortSignal;
  removeAbortListener?: () => void;
  resolve: (value: TResponse) => void;
  reject: (reason?: unknown) => void;
};

type ActiveTask<TRequest, TResponse> = {
  task: QueueTask<TRequest, TResponse>;
  timeoutId: ReturnType<typeof setTimeout> | null;
};

type WorkerQueueState<TRequest, TResponse> = {
  worker: Worker | null;
  queue: QueueTask<TRequest, TResponse>[];
  active: ActiveTask<TRequest, TResponse> | null;
  idleTimeoutId: ReturnType<typeof setTimeout> | null;
};

type WorkerRequest<TRequest> = {
  messageId: string;
  options: TRequest;
};

type WorkerSuccessResponse<TResponse> = {
  messageId: string;
  status: 'success';
  result: TResponse;
};

type WorkerErrorResponse = {
  messageId: string;
  status: 'error';
  error?: unknown;
};

type WorkerResponse<TResponse> = WorkerSuccessResponse<TResponse> | WorkerErrorResponse;

function toWorkerError(error: unknown) {
  if (error instanceof Error) {
    return error;
  }
  if (typeof error === 'string' && error.length > 0) {
    return new Error(error);
  }
  return new Error('Worker execution failed');
}

function toAbortError() {
  if (typeof DOMException !== 'undefined') {
    return new DOMException('Operation was aborted', 'AbortError');
  }
  const error = new Error('Operation was aborted');
  error.name = 'AbortError';
  return error;
}


export function useWorkerQueue<TRequest, TResponse>(
  key: string,
  createWorker: () => Worker,
  options?: {
    timeout?: number;
    maxQueueLength?: number;
    idleTimeout?: number;
  },
) {
  const timeout = options?.timeout;
  const maxQueueLength = options?.maxQueueLength;
  const idleTimeout = options?.idleTimeout ?? 0;

  const state = useState<WorkerQueueState<TRequest, TResponse>>(`workerQueue:${key}`, () => ({
    worker: null,
    queue: [],
    active: null,
    idleTimeoutId: null,
  }));

  function clearIdleTimeout() {
    if (state.value.idleTimeoutId) {
      clearTimeout(state.value.idleTimeoutId);
      state.value.idleTimeoutId = null;
    }
  }

  function scheduleIdleTermination() {
    clearIdleTimeout();
    if (!state.value.worker || state.value.active || state.value.queue.length > 0 || idleTimeout <= 0) {
      return;
    }
    state.value.idleTimeoutId = setTimeout(() => {
      if (!state.value.active && state.value.queue.length === 0) {
        terminateWorker();
      }
    }, idleTimeout);
  }

  function terminateWorker() {
    clearIdleTimeout();
    if (state.value.worker) {
      state.value.worker.terminate();
      state.value.worker = null;
    }
  }

  function clearTaskAbortListener(task: QueueTask<TRequest, TResponse>) {
    task.removeAbortListener?.();
    task.removeAbortListener = undefined;
  }

  function resolveTask(task: QueueTask<TRequest, TResponse>, value: TResponse) {
    clearTaskAbortListener(task);
    task.resolve(value);
  }

  function rejectTask(task: QueueTask<TRequest, TResponse>, reason: unknown) {
    clearTaskAbortListener(task);
    task.reject(reason);
  }

  function clearActiveTimeout(timeoutId: ReturnType<typeof setTimeout> | null) {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
  }

  function clearActiveTask(active: ActiveTask<TRequest, TResponse>) {
    clearActiveTimeout(active.timeoutId);
    state.value.active = null;
  }

  function failActiveTask(reason: unknown, options?: { terminateWorkerInstance?: boolean }) {
    const active = state.value.active;
    if (!active) {
      return;
    }
    clearActiveTask(active);
    if (options?.terminateWorkerInstance) {
      terminateWorker();
    }
    rejectTask(active.task, reason);
    processNext();
  }

  function ensureWorker() {
    if (state.value.worker) {
      return state.value.worker;
    }

    const worker = createWorker();
    worker.addEventListener('message', (e: MessageEvent<WorkerResponse<TResponse>>) => {
      const active = state.value.active;
      if (!active) {
        return;
      }
      if (e.data?.messageId !== active.task.messageId) {
        return;
      }

      clearActiveTask(active);
      if (e.data.status === 'success') {
        resolveTask(active.task, e.data.result);
      } else {
        rejectTask(active.task, toWorkerError(e.data.error));
      }
      processNext();
    });

    worker.addEventListener('error', (e: ErrorEvent) => {
      terminateWorker();
      failActiveTask(new Error(e.message || 'Worker execution failed'));
    });

    worker.addEventListener('messageerror', () => {
      terminateWorker();
      failActiveTask(new Error('Worker message deserialization failed'));
    });

    state.value.worker = worker;
    return worker;
  }

  function processNext() {
    clearIdleTimeout();
    if (!state.value.active && state.value.queue.length === 0) {
      scheduleIdleTermination();
      return;
    }
    if (state.value.active) {
      return;
    }

    const task = state.value.queue.shift()!;
    const worker = ensureWorker();
    const timeoutId = task.timeout !== undefined ? setTimeout(() => {
      if (!state.value.active || state.value.active.task.messageId !== task.messageId) {
        return;
      }

      failActiveTask(new Error('Worker timeout'), { terminateWorkerInstance: true });
    }, task.timeout) : null;

    state.value.active = { task: task, timeoutId };
    try {
      const request: WorkerRequest<TRequest> = {
        messageId: task.messageId,
        options: toRaw(task.request),
      };
      worker.postMessage(request);
    } catch (e) {
      failActiveTask(e, { terminateWorkerInstance: true });
    }
  }

  function terminate() {
    const active = state.value.active;
    if (active) {
      clearActiveTask(active);
      rejectTask(active.task, new Error('Worker terminated'));
    }

    if (state.value.queue.length > 0) {
      const pendingTasks = state.value.queue.splice(0, state.value.queue.length);
      for (const task of pendingTasks) {
        rejectTask(task, new Error('Worker terminated'));
      }
    }

    terminateWorker();
  }

  function run(request: TRequest, options?: { signal?: AbortSignal }) {
    if (import.meta.server) {
      return Promise.reject(new Error('Workers are only available in the browser'));
    }

    if (maxQueueLength !== undefined && state.value.queue.length >= maxQueueLength) {
      return Promise.reject(new Error(`Worker queue limit reached (${maxQueueLength})`));
    }

    return new Promise<TResponse>((resolve, reject) => {
      const signal = options?.signal;
      if (signal?.aborted) {
        reject(toAbortError());
        return;
      }

      const task: QueueTask<TRequest, TResponse> = {
        messageId: uuidv4(),
        request,
        timeout,
        signal,
        resolve,
        reject,
      };

      if (signal) {
        const onAbort = () => {
          const active = state.value.active;
          if (active?.task.messageId === task.messageId) {
            failActiveTask(toAbortError(), { terminateWorkerInstance: true });
            return;
          }

          const queueIndex = state.value.queue.findIndex(t => t.messageId === task.messageId);
          if (queueIndex >= 0) {
            state.value.queue.splice(queueIndex, 1);
            rejectTask(task, toAbortError());
          }
        };
        signal.addEventListener('abort', onAbort, { once: true });
        task.removeAbortListener = () => signal.removeEventListener('abort', onAbort);
      }

      state.value.queue.push(task);
      processNext();
    });
  }

  return {
    run,
    terminate,
  };
}
