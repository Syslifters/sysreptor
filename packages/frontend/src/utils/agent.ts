export enum MessageRole {
  USER = 'user',
  ASSISTANT = 'assistant',
  TOOL = 'tool',
}

export type SSEMessageEvent = {
  event?: string;
  data: string;
  id?: string;
};

export type AssistantMessage = {
  id: string;
  role: MessageRole.ASSISTANT;
  text?: string;
  reasoning?: string;
}

export type ChatHistoryEntry = {
  id: string;
  role: MessageRole;
  text?: string;
  reasoning?: string;
  tool_call?: ToolCall;
}

export enum ToolCallStatus {
  PENDING = 'pending',
  SUCCESS = 'success',
  ERROR = 'error',
}

export type ToolCall = {
  id: string;
  name: string;
  args: Record<string, any>;
  status: ToolCallStatus;
  timestamp: string;
  output?: any|null;
}

export enum StreamEventType {
  METADATA = 'metadata',
  TEXT = 'text',
  TOOL_CALL = 'tool_call',
  TOOL_CALL_STATUS = 'tool_call_status',
  ERROR = 'error',
}

export type StreamEvent = {
  type: StreamEventType.METADATA;
  content: {
    thread_id: string;
  }
} | {
  type: StreamEventType.TEXT;
  content: AssistantMessage;
} | {
  type: StreamEventType.TOOL_CALL;
  content: ToolCall;
} | {
  type: StreamEventType.TOOL_CALL_STATUS;
  content: Partial<ToolCall>;
} | {
  type: StreamEventType.ERROR;
  content: string;
};


/**
 * Parse Server-Sent Events (SSE) from a ReadableStream
 * @param stream The ReadableStream to parse
 * @param callbacks Callbacks for handling events
 */
export async function parseEventStream(
  stream: ReadableStream,
  callbacks: {
    onMessage?: (event: SSEMessageEvent) => void;
  },
  signal?: AbortSignal|null,
) {
  const reader = stream.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = '';

  function handleEvent(message: SSEMessageEvent) {
    if (message.event === 'error') {
      reader.cancel();
    }
    callbacks.onMessage?.(message);
  }
  
  // Current event being assembled
  let currentEvent: { event?: string; data: string[]; id?: string } = { data: [] };

  // Handle abort signal
  const abortHandler = () => {
    reader.cancel('Aborted by user').catch(() => {});
  };
  signal?.addEventListener('abort', abortHandler);

  try {
    while (true) {
      // Check if aborted before reading
      if (signal?.aborted) {
        throw new Error('Aborted by user');
      }
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      // Process complete lines in the buffer
      buffer += value;
      const lines = buffer.split('\n');
      // Keep the last incomplete line in the buffer
      buffer = lines.pop() || '';

      for (const line of lines) {
        // Remove carriage return if present
        const cleanLine = line.replace(/\r$/, '');

        // Empty line indicates end of event
        if (cleanLine === '') {
          if (currentEvent.data.length > 0) {
            // Dispatch the event
            const eventData = currentEvent.data.join('\n');
            handleEvent({
              event: currentEvent.event,
              data: eventData,
              id: currentEvent.id,
            });
          }
          // Reset for next event
          currentEvent = { data: [] };
          continue;
        }

        // Parse field and value
        const colonIndex = cleanLine.indexOf(':');
        if (colonIndex === -1) {
          // Line without colon - treat as field with empty value
          continue;
        }

        const field = cleanLine.substring(0, colonIndex);
        // Skip the colon and optional space
        let value = cleanLine.substring(colonIndex + 1);
        if (value.startsWith(' ')) {
          value = value.substring(1);
        }

        // Handle different field types
        if (field === 'event') {
          currentEvent.event = value;
        } else if (field === 'data') {
          currentEvent.data.push(value);
        } else if (field === 'id') {
          currentEvent.id = value;
        } else if (field === 'retry') {
          // Ignore retry field for now
        }
        // Comments (lines starting with :) are ignored
      }
    }

    // Process any remaining data in buffer
    if (buffer.trim()) {
      const cleanLine = buffer.replace(/\r$/, '');
      if (cleanLine !== '' && currentEvent.data.length > 0) {
        const eventData = currentEvent.data.join('\n');
        handleEvent({
          event: currentEvent.event,
          data: eventData,
          id: currentEvent.id,
        });
      }
    }
  } finally {
    signal?.removeEventListener('abort', abortHandler);
    reader.releaseLock();
  }
}

export async function fetchSSE(url: string, options: Partial<Parameters<typeof $fetch>[1]> & {
  onMessage?: (event: SSEMessageEvent) => void;
}) {
  const { onMessage, ...fetchOptions } = options;
  const stream = await $fetch<ReadableStream>(url, {
    ...fetchOptions,
    headers: {
      ...fetchOptions?.headers,
      'Accept': 'text/event-stream',
    },
    responseType: 'stream',
  });
  await parseEventStream(stream, { onMessage }, fetchOptions.signal);
}

export async function submitMessageStreamed(options: {
  body: {
    agent: string;
    id?: string|null;
    messages?: string[];
    context?: Record<string, string|null|undefined>;
    [key: string]: any;
  },
  messageHistory?: ChatHistoryEntry[],
  signal?: AbortSignal;
}) {
  const metadata = {
    thread_id: options.body.thread_id as string,
  };
  const messages = [] as ChatHistoryEntry[];
  const pendingToolCalls = [] as ToolCall[];

  await fetchSSE("/api/v1/utils/chat/", {
    method: "POST",
    body: options.body,
    signal: options.signal,
    onMessage(event) {
      const data = JSON.parse(event.data) as StreamEvent;

      if (data.type === StreamEventType.METADATA) {
        Object.assign(metadata, data.content);
      } else if (data.type === StreamEventType.TEXT) {
        // Reconstruct message by concatenating message chunks
        const currentMessage = messages.find(m => m.id === data.content.id);
        if (currentMessage) {
          currentMessage.text = (currentMessage.text || '') + (data.content.text || '');
          currentMessage.reasoning = (currentMessage.reasoning || '') + (data.content.reasoning || '');
        } else {
          const newMessage = reactive(data.content);
          messages.push(newMessage);
          options.messageHistory?.push(newMessage);
        }
      } else if (data.type === StreamEventType.TOOL_CALL) {
        options.messageHistory?.push(reactive({
          id: data.content.id,
          role: MessageRole.TOOL,
          tool_call: data.content,
        }));
      } else if (data.type === StreamEventType.TOOL_CALL_STATUS) {
        const toolCallMsg = options.messageHistory?.find(tc => tc.id === data.content.id);
        if (toolCallMsg?.tool_call) {
          Object.assign(toolCallMsg.tool_call!, data.content);
        }
      } else if (data.type === 'error') {
        throw new Error(data.content);
      }
    }
  });

  return {
    metadata,
    messages,
    pendingToolCalls,
    messageHistory: options.messageHistory,
  }
}


export type AiAgentStoreState = {
  threadId: string|null;
  messageHistory: ChatHistoryEntry[];
  currentRequest: {
    promise?: Promise<any>;
    abortController?: AbortController;
  }|null;
}


export function useAiAgentChat(options: {
  storeState: AiAgentStoreState;
  body: {
    agent: string,
    [key: string]: any;
  };
  threadId?: string;
}) {
  const inProgress = computed(() => !!options.storeState.currentRequest);

  async function loadHistory(params: Record<string, any>) {
    if (options.storeState.threadId) {
      // Already loaded
      return;
    }

    try {
      const promise = $fetch<{
        id: string;
        messages: ChatHistoryEntry[];
      }>(`/api/v1/utils/chat/${options.storeState.threadId || 'latest'}/`, { method: 'GET', params, });
      options.storeState.currentRequest = { promise };
      const response = await promise;
      options.storeState.threadId = response.id;
      options.storeState.messageHistory = response.messages;
    } catch {
      // ignore errors
    } finally {
      options.storeState.currentRequest = null;
    }
  }
  
  async function submitMessage(opts: { message: string, context?: Record<string, string|null|undefined>, agent?: string }) {
    const message = opts.message.trim();
    if (inProgress.value || !message) {
      return;
    }

    options.storeState.messageHistory.push({
      id: uuidv4(),
      role: MessageRole.USER,
      text: message,
    });

    try {
      const abortController = new AbortController();
      const promise = submitMessageStreamed({
        body: {
          ...options.body,
          id: options.storeState.threadId,
          messages: [message], 
          context: opts.context,
          agent: opts.agent || options.body.agent,
        },
        messageHistory: options.storeState.messageHistory,
        signal: abortController.signal,
      });
      options.storeState.currentRequest = { promise, abortController };
      const out = await promise;
      options.storeState.threadId = out.metadata.thread_id;

      if (abortController.signal.aborted) {
        return 'aborted';
      } else {
        return 'success';
      }
    } catch (error) {
      requestErrorToast({ error });
      return 'error';
    } finally {
      options.storeState.currentRequest = null;
    }
  }

  function abort() {
    options.storeState.currentRequest?.abortController?.abort();
    options.storeState.currentRequest = null;
  }
  onUnmounted(() => abort());

  function reset() {
    abort();
    options.storeState.threadId = null;
    options.storeState.messageHistory = [];
  }

  return {
    threadId: computed(() => options.storeState.threadId),
    messageHistory: computed(() => options.storeState.messageHistory),
    inProgress,
    submitMessage,
    loadHistory,
    reset,
    abort,
  }
}

