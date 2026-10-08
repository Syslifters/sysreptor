import type { PentestFinding, ProjectNote, ReportSection } from '#imports';

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
  timestamp?: string;
  text?: string;
  reasoning?: string;
}

export type ChatHistoryEntry = {
  id: string;
  role: MessageRole;
  timestamp?: string;
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
  content?: string;
  output?: any|null;
  subagentMessages?: ChatHistoryEntry[];
}

export function isLastAssistantMessageInTurn(
  messages: readonly ChatHistoryEntry[],
  index: number,
): boolean {
  const msg = messages[index];
  if (msg?.role !== MessageRole.ASSISTANT) {
    return false;
  }
  const next = messages[index + 1];
  return !next || next.role === MessageRole.USER;
}

export function isChatMessageStreaming(
  msg: ChatHistoryEntry,
  options: { inProgress: boolean; isLastMessage: boolean },
): boolean {
  if (!options.inProgress) {
    return false;
  }
  if (msg.role === MessageRole.TOOL) {
    return msg.tool_call?.status === ToolCallStatus.PENDING;
  }
  if (msg.role === MessageRole.ASSISTANT) {
    return options.isLastMessage;
  }
  return false;
}

export enum StreamEventType {
  METADATA = 'metadata',
  SNAPSHOT = 'snapshot',
  TEXT = 'text',
  TOOL_CALL = 'tool_call',
  TOOL_CALL_STATUS = 'tool_call_status',
  INTERRUPT = 'interrupt',
  ERROR = 'error',
  RUN_STATUS = 'run_status',
}

export type ChatInterrupt = {
  id: string;
  value: AskUserInterruptValue;
};

export type AskUserInterruptValue = {
  interrupt_type: 'ask_user';
  question: string;
  options: string[];
};

export type StreamEvent = {
  type: StreamEventType.METADATA;
  content: {
    thread_id: string;
  }
} | {
  type: StreamEventType.SNAPSHOT;
  content: {
    messages: ChatHistoryEntry[];
    interrupts: ChatInterrupt[];
    thread_id: string;
    run_id?: string|null;
    run_status?: string|null;
  };
} | {
  type: StreamEventType.TEXT;
  content: ChatHistoryEntry & { replace?: boolean };
  subagent?: string|null;
} | {
  type: StreamEventType.TOOL_CALL;
  content: ToolCall;
  subagent?: string|null;
} | {
  type: StreamEventType.TOOL_CALL_STATUS;
  content: Partial<ToolCall>;
  subagent?: string|null;
} | {
  type: StreamEventType.INTERRUPT;
  content: ChatInterrupt[];
} | {
  type: StreamEventType.ERROR;
  content: string;
} | {
  type: StreamEventType.RUN_STATUS;
  content: {
    status: string;
    error?: string|null;
    interrupts?: ChatInterrupt[];
  };
};

export type ApplyStreamState = {
  interrupts: ChatInterrupt[];
  error: string | null;
  runStatus: string | null;
};

function isRequestAborted(error: any): boolean {
  return Boolean(error?.options?.signal?.aborted || error?.name === 'AbortError' || error?.message === 'Aborted by user');
}

export function findToolCall(
  messages: ChatHistoryEntry[],
  toolCallId?: string|null,
): ToolCall|null {
  if (!toolCallId) {
    return null;
  }
  for (const m of messages) {
    if (m.role === MessageRole.TOOL && m.tool_call?.id === toolCallId) {
      return m.tool_call;
    }
    if (m.role === MessageRole.TOOL && m.tool_call?.subagentMessages) {
      const toolCall = findToolCall(m.tool_call.subagentMessages, toolCallId);
      if (toolCall) { 
        return toolCall;
      }
    }
  }
  return null;
}

function getSubagentMessageList(messages: ChatHistoryEntry[], subagent?: string | null): ChatHistoryEntry[] {
  if (!subagent) { 
    return messages;
  }
  const subagentToolCall = findToolCall(messages, subagent);
  return subagentToolCall?.subagentMessages ?? [];
}

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

/**
 * Apply one stream event onto messageHistory (mutates in place).
 * Returns true when a terminal run_status was received.
 */
export function applyStreamEvent(
  messageHistory: ChatHistoryEntry[],
  state: ApplyStreamState,
  data: StreamEvent,
): boolean {
  if (data.type === StreamEventType.METADATA) {
    // TODO: Handle metadata events
  } else if (data.type === StreamEventType.SNAPSHOT) {
    const snapshotMessages = (data.content.messages || []).map(m => reactive({ ...m }));
    const snapshotIds = new Set(snapshotMessages.map(m => m.id));
    // Keep a trailing optimistic user message not yet in the checkpoint
    const last = messageHistory[messageHistory.length - 1];
    const trailing = (
      last?.role === MessageRole.USER && !snapshotIds.has(last.id)
    ) ? [last] : [];
    messageHistory.splice(0, messageHistory.length, ...snapshotMessages, ...trailing);
    state.interrupts = data.content.interrupts || [];
  } else if (data.type === StreamEventType.TEXT) {
    // Reconcile optimistic local user message (same text, different id)
    if (
      data.content.role === MessageRole.USER
      && !data.subagent
      && !messageHistory.some(m => m.id === data.content.id)
    ) {
      const last = messageHistory[messageHistory.length - 1];
      if (
        last?.role === MessageRole.USER
        && last.text === data.content.text
        && last.id !== data.content.id
      ) {
        last.id = data.content.id;
        if (data.content.timestamp) {
          last.timestamp = data.content.timestamp;
        }
        return false;
      }
    }

    const messageList = getSubagentMessageList(messageHistory, data.subagent);
    const currentMessage = messageList.find(m => m.id === data.content.id);
    if (currentMessage) {
      if (data.content.replace) {
        Object.assign(currentMessage, data.content);
      } else {
        currentMessage.text = (currentMessage.text || '') + (data.content.text || '');
        currentMessage.reasoning = (currentMessage.reasoning || '') + (data.content.reasoning || '');
        if (data.content.timestamp && !currentMessage.timestamp) {
          currentMessage.timestamp = data.content.timestamp;
        }
      }
    } else {
      messageList.push(reactive(data.content));
    }
  } else if (data.type === StreamEventType.TOOL_CALL) {
    const messageList = getSubagentMessageList(messageHistory, data.subagent);
    if (!messageList.some(m => m.id === data.content.id)) {
      messageList.push(reactive({
        id: data.content.id,
        role: MessageRole.TOOL,
        timestamp: data.content.timestamp,
        tool_call: {
          ...data.content,
          subagentMessages: [],
        },
      }));
    }
  } else if (data.type === StreamEventType.TOOL_CALL_STATUS) {
    const toolCall = findToolCall(messageHistory, data.content.id);
    if (toolCall) {
      Object.assign(toolCall, data.content);
    }
  } else if (data.type === StreamEventType.INTERRUPT) {
    state.interrupts = data.content;
  } else if (data.type === StreamEventType.ERROR) {
    state.error = data.content;
  } else if (data.type === StreamEventType.RUN_STATUS) {
    state.runStatus = data.content.status;
    if (data.content.error) {
      state.error = data.content.error;
    }
    if (data.content.interrupts) {
      state.interrupts = data.content.interrupts;
    }
    return true;
  }
  return false;
}

/**
 * Subscribe to a thread's SSE stream (snapshot + live tail).
 */
export async function submitMessageStreamed(options: {
  url: string;
  messageHistory?: ChatHistoryEntry[];
  signal?: AbortSignal;
}) {
  const streamState: ApplyStreamState = {
    interrupts: [],
    error: null,
    runStatus: null,
  };
  const messageHistory = options.messageHistory ?? [];

  await fetchSSE(options.url, {
    method: 'GET',
    signal: options.signal,
    onMessage(event) {
      const data = JSON.parse(event.data) as StreamEvent;
      applyStreamEvent(messageHistory, streamState, data);
    },
  });

  return {
    messages: messageHistory,
    interrupts: streamState.interrupts,
    messageHistory,
    error: streamState.error,
    runStatus: streamState.runStatus,
  };
}


export type AiAgentStoreState = {
  threadId: string|null;
  messageHistory: ChatHistoryEntry[];
  interrupts: ChatInterrupt[];
  error: string|null;
  run: { id: string } | null;
  currentRequest: {
    promise?: Promise<any>;
    abortController?: AbortController;
    reconnectTimer?: ReturnType<typeof setTimeout>|null;
  }|null;
  changesState: {
    sessionStartIndex: number;
    historyReady: boolean;
    acceptedUpTo: Record<string, string>;
  };
}


export function useAiAgentChat(options: {
  storeState: AiAgentStoreState;
  body: {
    agent: string,
    [key: string]: any;
  };
  threadId?: string;
}) {
  const inProgress = computed(() => !!options.storeState.currentRequest || !!options.storeState.run);
  const changesState = computed(() => options.storeState.changesState);
  const currentSessionMessages = computed(() => options.storeState.messageHistory.slice(changesState.value.sessionStartIndex));

  function initChangesSession() {
    if (!changesState.value.historyReady) {
      // Only track changes made after history load (this browser session).
      changesState.value.sessionStartIndex = options.storeState.messageHistory.length;
      changesState.value.historyReady = true;
    }
  }

  function resetChanges() {
    changesState.value.sessionStartIndex = 0;
    changesState.value.historyReady = true;
    changesState.value.acceptedUpTo = {};
  }

  function acceptChange(filePath: string) {
    const latestTimestamp = getLatestWriteToolTimestamp(currentSessionMessages.value, filePath);
    if (!latestTimestamp) {
      return;
    }
    changesState.value.acceptedUpTo = {
      ...changesState.value.acceptedUpTo,
      [filePath]: latestTimestamp,
    };
  }

  const changedFiles = computed(() => {
    if (!changesState.value.historyReady) {
      return [];
    }
    return buildChangedFiles(
      currentSessionMessages.value,
      changesState.value.acceptedUpTo,
    );
  });

  function clearReconnectTimer() {
    const s = options.storeState;
    if (s.currentRequest?.reconnectTimer) {
      clearTimeout(s.currentRequest.reconnectTimer);
      s.currentRequest.reconnectTimer = null;
    }
  }

  async function attachToRun(threadId: string, runId: string) {
    const s = options.storeState;
    s.run = { id: runId };
    let reconnectAttempt = 0;
    const abortController = new AbortController();

    const promise = (async () => {
      while (!abortController.signal.aborted) {
        try {
          const out = await submitMessageStreamed({
            url: `/api/v1/utils/chat/${threadId}/stream/`,
            messageHistory: s.messageHistory,
            signal: abortController.signal,
          });
          s.interrupts = out.interrupts;
          s.error = out.error;
          s.run = null;
          return out;
        } catch (error: any) {
          if (isRequestAborted(error) || abortController.signal.aborted) {
            throw error;
          }
          const delay = Math.min(30000, 1000 * (2 ** reconnectAttempt));
          reconnectAttempt += 1;
          await new Promise<void>((resolve) => {
            if (s.currentRequest) {
              s.currentRequest.reconnectTimer = setTimeout(resolve, delay);
            } else {
              setTimeout(resolve, delay);
            }
          });
          clearReconnectTimer();
        }
      }
      return { runStatus: 'aborted', error: null, interrupts: s.interrupts };
    })();

    s.currentRequest = { promise, abortController, reconnectTimer: null };
    try {
      return await promise;
    } finally {
      if (s.currentRequest?.promise === promise) {
        s.currentRequest = null;
      }
    }
  }

  async function loadHistory(params: Record<string, any>, opts?: { force?: boolean }) {
    const s = options.storeState;
    if (s.threadId && !opts?.force) {
      // Already loaded
      if (s.run && !s.currentRequest) {
        void attachToRun(s.threadId, s.run.id);
      }
      initChangesSession();
      return;
    }

    try {
      const url = s.threadId
        ? `/api/v1/utils/chat/${s.threadId}/`
        : `/api/v1/utils/chat/latest/`;
      const promise = $fetch<{
        id: string;
        messages: ChatHistoryEntry[];
        interrupts?: ChatInterrupt[];
        run_id?: string|null;
        run_status?: string|null;
      }>(url, { method: 'GET', params });
      s.currentRequest = { promise };
      const response = await promise;
      s.threadId = response.id;
      s.messageHistory = response.messages;
      s.interrupts = response.interrupts ?? [];

      if (response.run_status === 'running' && response.run_id) {
        s.run = { id: response.run_id };
        s.currentRequest = null;
        void attachToRun(response.id, response.run_id);
      } else {
        s.run = null;
      }
    } catch {
      // ignore errors (e.g. no latest thread)
    } finally {
      if (s.currentRequest && !s.run) {
        s.currentRequest = null;
      }
    }
    initChangesSession();
  }

  async function startRun(body: Record<string, any>) {
    const s = options.storeState;
    try {
      const response = await $fetch<{ thread_id: string; run_id: string }>('/api/v1/utils/chat/', {
        method: 'POST',
        body,
      });
      s.threadId = response.thread_id;
      const out = await attachToRun(response.thread_id, response.run_id);
      if (out?.error || out?.runStatus === 'error') {
        return 'error';
      } else if (out?.runStatus === 'cancelled') {
        return 'aborted';
      }
      return 'success';
    } catch (error: any) {
      if (isRequestAborted(error)) {
        return 'aborted';
      }
      s.error = formatRequestError({ error, message: 'AI chat request failed' }) || 'Unexpected error';
      return 'error';
    }
  }

  async function submitMessage(opts: { message: string, context?: Record<string, string|null|undefined>, agent?: string, model?: string|null }) {
    const message = opts.message.trim();
    if (inProgress.value || !message) {
      return;
    }

    // User chose to send a new message instead of answering pending questions.
    options.storeState.interrupts = [];
    options.storeState.error = null;

    const messageId = uuidv4();
    options.storeState.messageHistory.push({
      id: messageId,
      role: MessageRole.USER,
      text: message,
    });

    return await startRun({
      ...options.body,
      id: options.storeState.threadId,
      messages: [message],
      context: opts.context,
      agent: opts.agent || options.body.agent,
      model: opts.model || options.body.model,
    });
  }

  async function resume(resumePayload: Record<string, any>) {
    if (inProgress.value || !options.storeState.threadId) {
      return;
    }

    options.storeState.error = null;

    return await startRun({
      ...options.body,
      id: options.storeState.threadId,
      resume: resumePayload,
    });
  }

  /** Abort only the local SSE subscription; the agent keeps running. */
  function detach() {
    clearReconnectTimer();
    options.storeState.currentRequest?.abortController?.abort();
    options.storeState.currentRequest = null;
  }

  /** Ask the server to stop the run, then wait for run_status. */
  async function cancel() {
    const s = options.storeState;
    const threadId = s.threadId;
    if (threadId && s.run) {
      try {
        await $fetch(`/api/v1/utils/chat/${threadId}/cancel/`, { 
          method: 'POST', 
          body: {},
        });
      } catch {
        // ignore
      }
      // Let the stream finish with run_status(cancelled)
      if (s.currentRequest?.promise) {
        try {
          await s.currentRequest.promise;
        } catch {
          // ignore
        }
      }
    } else {
      detach();
    }
    s.run = null;
  }
  onUnmounted(() => detach());

  function reset() {
    void cancel().finally(() => {
      options.storeState.threadId = null;
      options.storeState.messageHistory = [];
      options.storeState.interrupts = [];
      options.storeState.error = null;
      options.storeState.run = null;
      resetChanges();
    });
  }

  return {
    threadId: computed(() => options.storeState.threadId),
    messageHistory: computed(() => options.storeState.messageHistory),
    interrupts: computed(() => options.storeState.interrupts),
    error: computed(() => options.storeState.error),
    changedFiles,
    inProgress,
    submitMessage,
    resume,
    loadHistory,
    reset,
    cancel,
    detach,
    acceptChange,
  }
}


export type AgentChangedPage = {
  filePath: string;
  type: string;
  id: string;
  title: string;
  isCreated: boolean;
  diffTimestamp: string;
};

export function getToolFilePath(tool: ToolCall): string | null {
  if (['update_field_value', 'update_markdown_field'].includes(tool.name)) {
    return tool.args?.file_path || null;
  } else if (tool.name === 'create_finding' && tool.output?.id) {
    return `/project/reporting/findings/${tool.output.id}.yaml`;
  } else if (tool.name === 'create_note' && tool.output?.id) {
    return `/project/notes/${tool.output.id}.yaml`;
  } else {
    return null;
  }
}

export function parseProjectFilePath(filePath: string) {
  const findingMatch = filePath.match(/^\/project\/reporting\/findings\/([^/]+)\.yaml$/);
  if (findingMatch?.[1]) {
    return { type: 'finding', id: findingMatch[1] };
  }
  const sectionMatch = filePath.match(/^\/project\/reporting\/sections\/([^/]+)\.yaml$/);
  if (sectionMatch?.[1]) {
    return { type: 'section', id: sectionMatch[1] };
  }
  const noteMatch = filePath.match(/^\/project\/notes\/([^/]+)\.yaml$/);
  if (noteMatch?.[1]) {
    return { type: 'note', id: noteMatch[1] };
  }
  return null;
}

export function parseProjectImageName(imageRef: string | null | undefined): string | null {
  if (!imageRef || typeof imageRef !== 'string') {
    return null;
  }
  let filename = imageRef.trim();
  const match = filename.match(/\/images\/name\/([^)\s{]+)/);
  if (match?.[1]) {
    filename = match[1];
  }
  if (!filename || filename.includes('/')) {
    return null;
  }
  return filename;
}

export function getChangedPagePath(projectId: string, page: AgentChangedPage): string|undefined {
  let basePath;
  if (page.type === 'finding') {
    basePath = `/projects/${projectId}/reporting/findings/${page.id}/`;
  } else if (page.type === 'section') {
    basePath = `/projects/${projectId}/reporting/sections/${page.id}/`;
  } else if (page.type === 'note') {
    basePath = `/projects/${projectId}/notes/${page.id}/`;
  } else {
    return undefined;
  }
  
  if (!page.isCreated) {
    basePath += `history/${page.diffTimestamp}/`;
  }
  return basePath;
}

export function getPageTitle(
  fileRef: { type: string, id: string },
  titles: {
    findings: PentestFinding[];
    sections: ReportSection[];
    notes: ProjectNote[];
    fallbackTitle?: string;
  },
): string {
  if (fileRef.type === 'finding') {
    const finding = titles.findings.find(f => f.id === fileRef.id);
    return finding?.data?.title ?? titles.fallbackTitle ?? fileRef.id;
  } else if (fileRef.type === 'section') {
    const section = titles.sections.find(s => s.id === fileRef.id);
    return section?.label ?? titles.fallbackTitle ?? fileRef.id;
  } else if (fileRef.type === 'note') {
    const note = titles.notes.find(n => n.id === fileRef.id);
    return note?.title ?? titles.fallbackTitle ?? fileRef.id;
  } else {
    return titles.fallbackTitle ?? fileRef.id;
  }
}

function walkToolCalls(messages: ChatHistoryEntry[], callback: (tool: ToolCall) => void) {
  for (const m of messages) {
    if (m.role !== MessageRole.TOOL || !m.tool_call) {
      continue;
    }
    callback(m.tool_call);
    if (m.tool_call.subagentMessages?.length) {
      walkToolCalls(m.tool_call.subagentMessages, callback);
    }
  }
}

function isSuccessfulWriteTool(tool: ToolCall): boolean {
  const WRITE_TOOLS = new Set([
    'update_field_value',
    'update_markdown_field',
    'create_finding',
    'create_note',
  ]);
  return WRITE_TOOLS.has(tool.name)
    && tool.status === ToolCallStatus.SUCCESS
    && !!tool.timestamp
    && !!getToolFilePath(tool);
}

export function getLatestWriteToolTimestamp(
  messages: readonly ChatHistoryEntry[],
  filePath: string,
): string | null {
  let latest: string | null = null;
  walkToolCalls([...messages], (tool) => {
    if (!isSuccessfulWriteTool(tool) || getToolFilePath(tool) !== filePath) {
      return;
    }
    if (!latest || tool.timestamp > latest) {
      latest = tool.timestamp;
    }
  });
  return latest;
}

export function buildChangedFiles(
  messages: readonly ChatHistoryEntry[],
  acceptedUpTo: Record<string, string> = {},
) {
  const byPath = new Map<string, { 
    filePath: string,
    diffTimestamp: string,
    isCreated: boolean,
  }>();

  walkToolCalls([...messages], (tool) => {
    if (!isSuccessfulWriteTool(tool)) {
      return;
    }
    const filePath = getToolFilePath(tool)!;
    const acceptedUntil = acceptedUpTo[filePath];
    if (acceptedUntil && tool.timestamp <= acceptedUntil) {
      return;
    }

    const isCreate = tool.name === 'create_finding' || tool.name === 'create_note';
    const existing = byPath.get(filePath);
    if (existing) {
      if (tool.timestamp < existing.diffTimestamp) {
        existing.diffTimestamp = tool.timestamp;
      }
      existing.isCreated = existing.isCreated || isCreate;
    } else {
      byPath.set(filePath, { filePath, diffTimestamp: tool.timestamp, isCreated: isCreate });
    }
  });

  return Array.from(byPath.values());
}

