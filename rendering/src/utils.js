import { nextTick } from "vue";

export async function callForTicks(tickCount, tickCallback) {
  for (let i = 0; i < tickCount; i++) {
    await nextTick();
    tickCallback();
  }
}


/**
 * Compatibility layer to allow passing an array of items to v-slot at top level.
 * This function returns a slot value that is both an array (old syntax) and an object with an "items" property (new syntax).
 */
export function slotDataArray(items) {
  const data = [...items];
  data.items = data;
  return data;
}
