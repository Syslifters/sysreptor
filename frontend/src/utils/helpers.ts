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

export function focusElement(id?: string, options?: { scroll?: ScrollIntoViewOptions }) {
  if (id?.startsWith('#')) {
    id = id.slice(1);
  }
  if (!id) {
    return;
  }

  const elField = document.getElementById(id);
  const elFieldInput = (elField?.querySelector('*[contenteditable]') || elField?.querySelector('input')) as HTMLInputElement|undefined;

  if (elField && elFieldInput) {
    if (options?.scroll) {
      elField.scrollIntoView(options.scroll);
      elField.focus({ preventScroll: true });
    } else {
      elFieldInput.focus();
    }
  } else if (elField) {
    elField.scrollIntoView(options?.scroll);
  }
}

export function useAutofocus(ready: Ref<any>|(() => any), fallbackId?: string) {
  const route = useRoute();

  const isMounted = ref(false);
  onMounted(() => {
    isMounted.value = true;
  });
  const isReady = ref(false);
  watch(ready, (val) => {
    isReady.value = !!val;
  }, { immediate: true });
  const isLoaded = computed(() => isMounted.value && isReady.value);

  whenever(isLoaded, async () => {
    await nextTick();
    focusElement(route.hash || fallbackId);
  }, { immediate: true, once: true });
}
