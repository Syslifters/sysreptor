onmessage = (e: MessageEvent<{ pattern: RegExp, value: string }>) => {
  const res = e.data.pattern.test(e.data.value);
  postMessage(res);
};
