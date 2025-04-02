import { nextTick, ref, type ComponentInternalInstance } from "vue";

export async function callForTicks(tickCount: number, tickCallback: () => void) {
  for (let i = 0; i < tickCount; i++) {
    await nextTick();
    tickCallback();
  }
}


/**
 * Compatibility layer to allow passing an array of items to v-slot at top level.
 * This function returns a slot value that is both an array (old syntax) and an object with an "items" property (new syntax).
 */
export function slotDataArray<T>(items: T[]) {
  const data = [...items] as (T[]) & { items: T[] };
  data.items = data;
  return data;
}


export function* getChildElementsRecursive(node: Node): Generator<Element> {
  if (node.nodeType === Node.ELEMENT_NODE) {
    yield node as Element;
  }
  for (const child of Array.from(node.childNodes)) {
    yield* getChildElementsRecursive(child);
  }
}


export function getAllElements(vm: ComponentInternalInstance|null, querySelector: string): HTMLElement[] {
  return vm?.root.vnode.el?.querySelectorAll(querySelector) || [];
}


export const pendingRenderTasks = ref<Promise<void>[]>([]);
export function useRenderTask(fn: () => Promise<void>) {
  return async () => {
    const t = fn();
    pendingRenderTasks.value.push(t);
    return await t;
  }
}