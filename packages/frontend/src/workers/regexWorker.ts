onmessage = (e: MessageEvent<{ messageId: string, options: { pattern: RegExp, value: string } }>) => {
  try {
    const result = e.data.options.pattern.test(e.data.options.value);
    postMessage({ messageId: e.data.messageId, status: 'success', result })
  } catch (error) {
    postMessage({ messageId: e.data.messageId, status: 'error', error });
  }
};
