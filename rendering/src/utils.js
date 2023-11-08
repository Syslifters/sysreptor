import { nextTick } from "vue";

export async function callForTicks(tickCount, tickCallback) {
  for (let i = 0; i < tickCount; i++) {
    await nextTick();
    tickCallback();
  }
}
