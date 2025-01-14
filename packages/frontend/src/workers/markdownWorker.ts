import { renderMarkdownToHtml } from "@sysreptor/markdown";

onmessage = (e: MessageEvent<{ messageId: string, options: Parameters<typeof renderMarkdownToHtml>[0] }>) => {
  try {
    const result = renderMarkdownToHtml(e.data.options);
    postMessage({ messageId: e.data.messageId, status: 'success', result })
  } catch (error) {
    postMessage({ messageId: e.data.messageId, status: 'error', error });
  }
};
