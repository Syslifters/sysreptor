
export async function callForTicks(tickCount, tickFn, tickCallback) {
  for (let i = 0; i < tickCount; i++) {
    await tickFn();
    tickCallback();
  }
}
