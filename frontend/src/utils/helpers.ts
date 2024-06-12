import { setWith, clone, cloneDeep } from "lodash-es";

/**
 * Immutable version of lodash.set
 */
export function setNested(obj: any, path: string|string[], value: any) {
  return setWith(clone(obj), path, value, clone);
}

export function computedThrottled<T>(fn: () => T, options: { throttle: number }) {
  const computedOriginal = computed<T>(fn);
  const valueThrottled = ref<T>(computedOriginal.value) as Ref<T>;
  watchThrottled(computedOriginal, () => {
    const val = cloneDeep(toRaw(computedOriginal.value));
    valueThrottled.value = val;
  }, { deep: true, immediate: true, throttle: options.throttle });
  return valueThrottled;
}
