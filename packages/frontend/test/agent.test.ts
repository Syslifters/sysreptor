import { describe, it, expect, vi } from 'vitest';
import { mockNuxtImport } from '@nuxt/test-utils/runtime';
import {
  MessageRole,
  StreamEventType,
  ToolCallStatus,
  applyStreamEvent,
  buildChangedFiles,
  getToolFilePath,
  parseProjectFilePath,
  parseProjectImageName,
  submitMessageStreamed,
  type ChatHistoryEntry,
  type StreamEvent, type ToolCall 
} from '~/utils/agent';

const { mockFetch, mockChatStream } = vi.hoisted(() => {
  const mockFetch = vi.fn();

  function mockChatStream(events: StreamEvent[]) {
    mockFetch.mockReset();
    mockFetch.mockImplementation(async (url: string, opts?: { method?: string; responseType?: string }) => {
      if (url.includes('/stream/') && opts?.method === 'GET' && opts?.responseType === 'stream') {
        return new ReadableStream({
          start(controller) {
            const body = events.map(e => `event: ${e.type}\ndata: ${JSON.stringify(e)}\n\n`).join('');
            controller.enqueue(new TextEncoder().encode(body));
            controller.close();
          },
        });
      }
      throw new Error(`Unexpected $fetch call: ${url}`);
    });
  }

  return { mockFetch, mockChatStream };
});

mockNuxtImport('$fetch', () => mockFetch);

describe('agentStreaming', () => {
  describe('submitMessageStreamed', () => {
    it('parses a full backend turn with snapshot, text chunks, tool_call, and tool_call_status', async () => {
      const assistantId = 'asst-1';
      const toolCallId = 'tool-1';
      const finalAssistantId = 'asst-2';
      const toolArgs = {
        file_path: '/project/reporting/sections/exec.yaml',
        field: 'data.summary',
        value: 'New summary',
      };

      mockChatStream([
        {
          type: StreamEventType.SNAPSHOT,
          content: {
            messages: [],
            interrupts: [],
            run_id: 'run-1',
            run_status: 'running',
          },
        },
        { type: StreamEventType.TEXT, content: { id: 'user-1', role: MessageRole.USER, text: 'Update it', replace: true } },
        { type: StreamEventType.TEXT, content: { id: assistantId, role: MessageRole.ASSISTANT, text: 'Let me ' }, subagent: null },
        { type: StreamEventType.TEXT, content: { id: assistantId, role: MessageRole.ASSISTANT, text: 'update.' }, subagent: null },
        {
          type: StreamEventType.TOOL_CALL,
          content: {
            id: toolCallId,
            name: 'update_field_value',
            args: toolArgs,
            status: ToolCallStatus.PENDING,
            timestamp: '2026-01-01T10:00:00+00:00',
            output: null,
          },
          subagent: null,
        },
        {
          type: StreamEventType.TOOL_CALL_STATUS,
          content: {
            id: toolCallId,
            name: 'update_field_value',
            status: ToolCallStatus.SUCCESS,
            output: {},
            timestamp: '2026-01-01T10:00:01+00:00',
          },
          subagent: null,
        },
        { type: StreamEventType.TEXT, content: { id: finalAssistantId, role: MessageRole.ASSISTANT, text: 'Done.' }, subagent: null },
        { type: StreamEventType.RUN_STATUS, content: { status: 'completed' } },
      ]);

      const messageHistory: ChatHistoryEntry[] = [];
      const result = await submitMessageStreamed({
        url: '/api/v1/utils/chat/thread-123/stream/',
        messageHistory,
      });

      expect(result.status).toBe('completed');

      const assistant = messageHistory.find(m => m.id === assistantId);
      expect(assistant?.text).toBe('Let me update.');

      const toolMsg = messageHistory.find(m => m.role === MessageRole.TOOL);
      expect(toolMsg?.tool_call?.status).toBe(ToolCallStatus.SUCCESS);
      expect(toolMsg?.tool_call?.args).toEqual(toolArgs);
      expect(toolMsg?.tool_call?.output).toEqual({});

      const finalAssistant = messageHistory.find(m => m.id === finalAssistantId);
      expect(finalAssistant?.text).toBe('Done.');
    });

    it('snapshot replaces history but keeps trailing optimistic user message', () => {
      const messageHistory: ChatHistoryEntry[] = [
        { id: 'local-user', role: MessageRole.USER, text: 'Hi' },
      ];
      const state = { interrupts: [], error: null as string | null, status: null as string | null };
      applyStreamEvent(messageHistory, state, {
        type: StreamEventType.SNAPSHOT,
        content: {
          messages: [
            { id: 'prev', role: MessageRole.ASSISTANT, text: 'Earlier' },
          ],
          interrupts: [],
          run_id: 'run-1',
          run_status: 'running',
        },
      });
      expect(messageHistory.map(m => m.id)).toEqual(['prev', 'local-user']);
    });

    it('replace snapshots overwrite streamed text', () => {
      const messageHistory: ChatHistoryEntry[] = [];
      const state = { interrupts: [], error: null as string | null, status: null as string | null };
      applyStreamEvent(messageHistory, state, {
        type: StreamEventType.TEXT,
        content: { id: 'a1', role: MessageRole.ASSISTANT, text: 'partial' },
      });
      applyStreamEvent(messageHistory, state, {
        type: StreamEventType.TEXT,
        content: { id: 'a1', role: MessageRole.ASSISTANT, text: 'full text', replace: true },
      });
      expect(messageHistory[0]?.text).toBe('full text');
    });

    it('accumulates incremental text and reasoning chunks for the same message id', async () => {
      const assistantId = 'asst-1';

      mockChatStream([
        {
          type: StreamEventType.SNAPSHOT,
          content: { messages: [], interrupts: [], run_id: 'run-1', run_status: 'running' },
        },
        {
          type: StreamEventType.TEXT,
          content: {
            id: assistantId,
            role: MessageRole.ASSISTANT,
            reasoning: 'think ',
            timestamp: '2026-01-01T10:00:00+00:00',
          },
          subagent: null,
        },
        { type: StreamEventType.TEXT, content: { id: assistantId, role: MessageRole.ASSISTANT, reasoning: 'more' }, subagent: null },
        { type: StreamEventType.TEXT, content: { id: assistantId, role: MessageRole.ASSISTANT, text: 'Hello ' }, subagent: null },
        { type: StreamEventType.TEXT, content: { id: assistantId, role: MessageRole.ASSISTANT, text: 'world' }, subagent: null },
      ]);

      const messageHistory: ChatHistoryEntry[] = [];
      await submitMessageStreamed({
        url: '/api/v1/utils/chat/thread-1/stream/',
        messageHistory,
      });

      expect(messageHistory).toHaveLength(1);
      expect(messageHistory[0].reasoning).toBe('think more');
      expect(messageHistory[0].text).toBe('Hello world');
      expect(messageHistory[0].timestamp).toBe('2026-01-01T10:00:00+00:00');
    });

    it('routes subagent events into the parent task tool call subagentMessages', async () => {
      const taskId = 'task-1';

      mockChatStream([
        {
          type: StreamEventType.SNAPSHOT,
          content: { messages: [], interrupts: [], run_id: 'run-1', run_status: 'running' },
        },
        {
          type: StreamEventType.TOOL_CALL,
          content: {
            id: taskId,
            name: 'task',
            args: { description: 'Do work' },
            status: ToolCallStatus.PENDING,
            timestamp: '2026-01-01T10:00:00+00:00',
            output: null,
          },
          subagent: null,
        },
        {
          type: StreamEventType.TEXT,
          content: { id: 'sub-asst', role: MessageRole.ASSISTANT, text: 'Subagent reply' },
          subagent: taskId,
        },
        {
          type: StreamEventType.TOOL_CALL,
          content: {
            id: 'sub-tool',
            name: 'update_field_value',
            args: { file_path: '/project/reporting/findings/f1.yaml' },
            status: ToolCallStatus.PENDING,
            timestamp: '2026-01-01T10:00:01+00:00',
            output: null,
          },
          subagent: taskId,
        },
      ]);

      const messageHistory: ChatHistoryEntry[] = [];
      await submitMessageStreamed({
        url: '/api/v1/utils/chat/thread-1/stream/',
        messageHistory,
      });

      expect(messageHistory).toHaveLength(1);
      expect(messageHistory[0].role).toBe(MessageRole.TOOL);
      expect(messageHistory[0].tool_call?.name).toBe('task');

      const subagentMessages = messageHistory[0].tool_call?.subagentMessages ?? [];
      expect(subagentMessages).toHaveLength(2);
      expect(subagentMessages[0].text).toBe('Subagent reply');
      expect(subagentMessages[1].role).toBe(MessageRole.TOOL);
      expect(subagentMessages[1].tool_call?.name).toBe('update_field_value');

      expect(messageHistory.some(m => m.id === 'sub-asst')).toBe(false);
    });

    it('routes analyze_image subagent events into the parent tool call subagentMessages', async () => {
      const analyzeId = 'analyze-image-1';

      mockChatStream([
        {
          type: StreamEventType.SNAPSHOT,
          content: { messages: [], interrupts: [], run_id: 'run-1', run_status: 'running' },
        },
        {
          type: StreamEventType.TOOL_CALL,
          content: {
            id: analyzeId,
            name: 'analyze_image',
            args: { image: 'file0.png' },
            status: ToolCallStatus.PENDING,
            timestamp: '2026-01-01T10:00:00+00:00',
            output: null,
          },
          subagent: null,
        },
        {
          type: StreamEventType.TEXT,
          content: { id: 'vision-asst', role: MessageRole.ASSISTANT, text: 'SQL error visible' },
          subagent: analyzeId,
        },
        {
          type: StreamEventType.TOOL_CALL_STATUS,
          content: {
            id: analyzeId,
            name: 'analyze_image',
            status: ToolCallStatus.SUCCESS,
            content: 'SQL error visible',
            output: { image: 'file0.png', model: 'vision-model' },
            timestamp: '2026-01-01T10:00:01+00:00',
          },
        },
      ]);

      const messageHistory: ChatHistoryEntry[] = [];
      await submitMessageStreamed({
        url: '/api/v1/utils/chat/thread-1/stream/',
        messageHistory,
      });

      expect(messageHistory).toHaveLength(1);
      expect(messageHistory[0].role).toBe(MessageRole.TOOL);
      expect(messageHistory[0].tool_call?.name).toBe('analyze_image');
      expect(messageHistory[0].tool_call?.status).toBe(ToolCallStatus.SUCCESS);
      expect(messageHistory[0].tool_call?.content).toBe('SQL error visible');

      const subagentMessages = messageHistory[0].tool_call?.subagentMessages ?? [];
      expect(subagentMessages).toHaveLength(1);
      expect(subagentMessages[0].text).toBe('SQL error visible');
      expect(messageHistory.some(m => m.id === 'vision-asst')).toBe(false);
    });

    it('returns the error event content and does not append to history', async () => {
      mockChatStream([
        {
          type: StreamEventType.SNAPSHOT,
          content: { messages: [], interrupts: [], run_id: 'run-1', run_status: 'running' },
        },
        { type: StreamEventType.ERROR, content: 'Incorrect API key provided' },
      ]);

      const messageHistory: ChatHistoryEntry[] = [
        { id: 'u1', role: MessageRole.USER, text: 'hello' },
      ];
      const result = await submitMessageStreamed({
        url: '/api/v1/utils/chat/thread-err/stream/',
        messageHistory,
      });

      expect(result.error).toBe('Incorrect API key provided');
      // Snapshot cleared history (no messages in snapshot); trailing user kept
      expect(messageHistory).toHaveLength(1);
      expect(messageHistory[0].role).toBe(MessageRole.USER);
    });
  });
});


function toolMessage(toolCall: Partial<ToolCall> & Pick<ToolCall, 'id' | 'name'>): ChatHistoryEntry {
  return {
    id: toolCall.id,
    role: MessageRole.TOOL,
    tool_call: {
      args: {},
      status: ToolCallStatus.SUCCESS,
      timestamp: '2026-01-01T10:00:00+00:00',
      ...toolCall,
    } as ToolCall,
  };
}

describe('agentChanges', () => {
  describe('getToolFilePath', () => {
    it('returns file_path for update tools', () => {
      expect(getToolFilePath({
        id: '1',
        name: 'update_field_value',
        args: { file_path: '/project/reporting/sections/exec.yaml' },
        status: ToolCallStatus.SUCCESS,
        timestamp: '',
      })).toBe('/project/reporting/sections/exec.yaml');
    });

    it('derives file_path for create_finding', () => {
      expect(getToolFilePath({
        id: '1',
        name: 'create_finding',
        args: {},
        output: { id: 'abc-123', title: 'New Finding' },
        status: ToolCallStatus.SUCCESS,
        timestamp: '',
      })).toBe('/project/reporting/findings/abc-123.yaml');
    });
  });

  describe('parseProjectFilePath', () => {
    it('parses finding, section, and note paths', () => {
      expect(parseProjectFilePath('/project/reporting/findings/f1.yaml')).toEqual({ type: 'finding', id: 'f1' });
      expect(parseProjectFilePath('/project/reporting/sections/s1.yaml')).toEqual({ type: 'section', id: 's1' });
      expect(parseProjectFilePath('/project/notes/n1.yaml')).toEqual({ type: 'note', id: 'n1' });
    });
  });

  describe('parseProjectImageName', () => {
    it('parses bare names, paths, and markdown image refs', () => {
      expect(parseProjectImageName('image.png')).toBe('image.png');
      expect(parseProjectImageName('/images/name/image.png')).toBe('image.png');
      expect(parseProjectImageName('![shot](/images/name/image.png)')).toBe('image.png');
      expect(parseProjectImageName('![shot](/images/name/image.png){width="auto"}')).toBe('image.png');
    });

    it('rejects invalid image refs', () => {
      expect(parseProjectImageName('')).toBeNull();
      expect(parseProjectImageName('/images/name/missing/path.png')).toBeNull();
      expect(parseProjectImageName('folder/image.png')).toBeNull();
      expect(parseProjectImageName(null)).toBeNull();
    });
  });

  describe('buildChangedFiles', () => {
    it('aggregates changes across multiple agent turns', () => {
      const sessionMessages: ChatHistoryEntry[] = [
        { id: 'u1', role: MessageRole.USER, text: 'first' },
        toolMessage({
          id: 't1',
          name: 'update_field_value',
          args: { file_path: '/project/reporting/findings/f1.yaml' },
          timestamp: '2026-01-01T10:00:00+00:00',
        }),
        { id: 'u2', role: MessageRole.USER, text: 'second' },
        toolMessage({
          id: 't2',
          name: 'update_field_value',
          args: { file_path: '/project/reporting/sections/s1.yaml' },
          timestamp: '2026-01-01T11:00:00+00:00',
        }),
      ];

      const files = buildChangedFiles(sessionMessages);
      expect(files).toHaveLength(2);
      expect(files.map(f => f.filePath).sort()).toEqual([
        '/project/reporting/findings/f1.yaml',
        '/project/reporting/sections/s1.yaml',
      ]);
    });

    it('uses earliest tool timestamp per file', () => {
      const sessionMessages: ChatHistoryEntry[] = [
        { id: 'u1', role: MessageRole.USER, text: 'go' },
        toolMessage({
          id: 't1',
          name: 'update_field_value',
          args: { file_path: '/project/reporting/findings/f1.yaml' },
          timestamp: '2026-01-01T10:00:00+00:00',
        }),
        { id: 'u2', role: MessageRole.USER, text: 'again' },
        toolMessage({
          id: 't2',
          name: 'update_markdown_field',
          args: { file_path: '/project/reporting/findings/f1.yaml' },
          timestamp: '2026-01-01T11:00:00+00:00',
        }),
      ];

      const files = buildChangedFiles(sessionMessages);
      expect(files).toHaveLength(1);
      expect(files[0].diffTimestamp).toBe('2026-01-01T10:00:00+00:00');
    });

    it('ignores failed tools', () => {
      const sessionMessages: ChatHistoryEntry[] = [
        { id: 'u1', role: MessageRole.USER, text: 'go' },
        toolMessage({
          id: 't1',
          name: 'update_field_value',
          args: { file_path: '/project/reporting/findings/f1.yaml' },
          status: ToolCallStatus.ERROR,
        }),
      ];
      expect(buildChangedFiles(sessionMessages)).toHaveLength(0);
    });

    it('hides accepted changes but shows later edits to the same file', () => {
      const filePath = '/project/reporting/findings/f1.yaml';
      const sessionMessages: ChatHistoryEntry[] = [
        { id: 'u1', role: MessageRole.USER, text: 'first' },
        toolMessage({
          id: 't1',
          name: 'update_field_value',
          args: { file_path: filePath },
          timestamp: '2026-01-01T10:00:00+00:00',
        }),
        { id: 'u2', role: MessageRole.USER, text: 'second' },
        toolMessage({
          id: 't2',
          name: 'update_field_value',
          args: { file_path: filePath },
          timestamp: '2026-01-01T11:00:00+00:00',
        }),
      ];

      const accepted = { f1: '2026-01-01T10:00:00+00:00' };
      const files = buildChangedFiles(sessionMessages, accepted);
      expect(files).toHaveLength(1);
      expect(files[0].diffTimestamp).toBe('2026-01-01T11:00:00+00:00');
    });

    it('includes nested subagent write tools', () => {
      const messages: ChatHistoryEntry[] = [
        { id: 'u1', role: MessageRole.USER, text: 'go' },
        toolMessage({
          id: 'task-1',
          name: 'task',
          args: { description: 'edit' },
          subagentMessages: [
            toolMessage({
              id: 't-nested',
              name: 'update_field_value',
              args: { file_path: '/project/reporting/findings/f1.yaml' },
              timestamp: '2026-01-01T10:00:00+00:00',
            }),
          ],
        }),
      ];
      const files = buildChangedFiles(messages);
      expect(files).toHaveLength(1);
      expect(files[0].filePath).toBe('/project/reporting/findings/f1.yaml');
    });

    it('create then delete', () => {
      const sessionMessages: ChatHistoryEntry[] = [
        { id: 'u1', role: MessageRole.USER, text: 'create then delete' },
        toolMessage({
          id: 't1',
          name: 'create_finding',
          args: {},
          output: { id: 'f1', title: 'Finding Title' },
          timestamp: '2026-01-01T10:00:00+00:00',
        }),
        toolMessage({
          id: 't2',
          name: 'delete',
          args: { file_path: '/project/reporting/findings/f1.yaml' },
          output: { id: 'f1', title: 'Finding Title' },
          timestamp: '2026-01-01T11:00:00+00:00',
        }),
      ];
      const files = buildChangedFiles(sessionMessages);
      expect(files).toHaveLength(1);
      expect(files[0]).toMatchObject({
        filePath: '/project/reporting/findings/f1.yaml',
        isDeleted: true,
        isCreated: true,
        diffTimestamp: '2026-01-01T10:00:00+00:00',
        title: 'Finding Title',
      });
    });
  });

});
