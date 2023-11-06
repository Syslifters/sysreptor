onmessage = (e: MessageEvent) => {
  const { pattern, value }: { pattern: RegExp, value: string } = e.data;
  const res = pattern.test(value);
  postMessage(res);
};
