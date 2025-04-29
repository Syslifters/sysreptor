import { setWith, clone, cloneDeep, sampleSize, isEqual, isObject } from "lodash-es";
export { decode as base64decode, encode as base64encode } from 'base64-arraybuffer';
export { default as fileDownload } from 'js-file-download';
export { default as urlJoin } from 'url-join';
export { v4 as uuidv4 } from "uuid";

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

export function computedCached<T>(fn: () => T) {
  return computed<T>((oldValue) => {
    const newValue = fn();
    return (oldValue && isEqual(oldValue, newValue)) ? oldValue : newValue;
  });
}

export function optimizedUpdateReactiveList<T>(newValue: T[], oldValue: T[]|undefined, key: (v: T) => any) {
  if (oldValue && isEqual(oldValue?.map(key), newValue.map(key))) {
    // Number of comments and order is the same: only update properties
    for (let i = 0; i < newValue.length; i++) {
      if (!isEqual(oldValue[i], newValue[i])) {
        if (isObject(oldValue[i]) && isObject(newValue[i])) {
          Object.assign(oldValue[i]!, newValue[i]!);
        } else {
          oldValue[i] = newValue[i]!;
        }
      }
    }
    return oldValue;
  } else {
    return newValue;
  }
}

export function computedList<T>(fn: () => T[], getItemKey?: (v: T) => any): Ref<T[]> {
  getItemKey = getItemKey || ((v: T) => v);

  const cachedValue = ref<T[]>([]) as Ref<T[]>;
  watchEffect(() => {
    const newValue = fn();
    cachedValue.value = optimizedUpdateReactiveList(newValue, cachedValue.value, getItemKey);
  })
  return cachedValue;
}


export function useKeyboardShortcut(shortcut: string, handler: (event: KeyboardEvent) => void) {
  function onKeyDown(event: KeyboardEvent) {
    const keys = shortcut.split('+');
    for (const k of keys) {
      if (!(
        (k === 'ctrl' && event.ctrlKey) ||
        (k === 'alt' && event.altKey) ||
        (k === 'shift' && event.shiftKey) ||
        (k === 'meta' && event.metaKey) ||
        (k === event.key.toLowerCase())
      )) {
        return;
      }
    }

    event.preventDefault();
    handler(event);
  }
  useEventListener(window, 'keydown', onKeyDown, { passive: false });
}

function* positions(node: any, isLineStart = true): Generator<{ node: Node, offset: number, text: string }> {
  let child = node.firstChild;
  let offset = 0;
  yield { node, offset, text: (!isLineStart && node.tagName === 'DIV') ? '\n' : '' };
  while (child != null) {
    if (child.nodeType === Node.TEXT_NODE) {
      yield { node: child, offset: 0 / 0, text: child.data };
      isLineStart = false;
    } else {
      isLineStart = yield * positions(child, isLineStart);
    }
    child = child.nextSibling;
    offset += 1;
    yield { node, offset, text: '' };
  }
  return isLineStart;
}

function getCaretPosition(contenteditable: HTMLElement, textPosition: number) {
  let textOffset = 0;
  let lastNode = null;
  let lastOffset = 0;
  for (const p of positions(contenteditable)) {
    if (p.text.length > textPosition - textOffset) {
      return { node: p.node, offset: p.node.nodeType === Node.TEXT_NODE ? textPosition - textOffset : p.offset };
    }
    textOffset += p.text.length;
    lastNode = p.node;
    lastOffset = p.node.nodeType === Node.TEXT_NODE ? p.text.length : p.offset;
  }
  return { node: lastNode!, offset: lastOffset };
}

export function focusElement(id?: string, options?: { scroll?: ScrollIntoViewOptions }) {
  if (id?.startsWith('#')) {
    id = id.slice(1);
  }
  if (!id) {
    return;
  }
  const idParts = id.split(':');
  id = idParts[0]!;
  const idParams = new URLSearchParams(idParts.slice(1).join(':'));

  const elField = document.getElementById(id);
  const elFieldInput = (elField?.querySelector('*[contenteditable]') || elField?.querySelector('input')) as HTMLInputElement|undefined;

  if (elField && elFieldInput) {
    const offset = Number.parseInt(idParams.get('offset') || '');
    if (!isNaN(offset) && offset >= 0) {
      const { node, offset: textOffset } = getCaretPosition(elFieldInput, offset);
      const range = document.createRange();
      range.setStart(node, textOffset);
      range.collapse(true);

      node.parentElement?.scrollIntoView(options?.scroll);
      elFieldInput.focus({ preventScroll: true });
      
      const selection = document.getSelection();
      selection?.removeAllRanges();
      selection?.addRange(range)
    } else if (options?.scroll) {
      elField.scrollIntoView(options.scroll);
      elField.focus({ preventScroll: true });
    } else {
      elFieldInput.focus();
    }
  } else if (elField) {
    elField.scrollIntoView(options?.scroll);
  }
}

export function useAutofocus(ready: Ref<any>|(() => any), fallbackId?: string, onAutofocus?: (id?: string) => void) {
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
    const id = route.hash || fallbackId;
    focusElement(route.hash || fallbackId);
    onAutofocus?.(id);
  }, { immediate: true, once: true });
}


export function copyToClipboard(text: string) {
  window.navigator.clipboard.writeText(text);
}


export function useAbortController<T>(performFetch: (fetchOptions: { signal: AbortSignal }) => Promise<T>) {
  const abortController = ref<AbortController|null>(null);
  const pending = computed(() => !!abortController.value);

  function abort() {
    if (abortController.value) {
      abortController.value.abort();
      abortController.value = null;
    }
  }

  async function run() {
    abort();

    try {
      abortController.value = new AbortController();
      return await performFetch({ signal: abortController.value.signal });
    } finally {
      abortController.value = null;
    }
  }

  useEventListener(window, 'beforeunload', abort);
  onUnmounted(() => abort());

  return {
    run,
    abort,
    abortController,
    pending,
  }
}

export function generateRandomPassword() {
  // Charset does not contain similar-looking characters and numbers; removed: 0,O, 1,l,I
  const charset = '23456789' + 'abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ' + '!#%&+-_';
  return sampleSize(charset, 20).join('');
}


export async function wait(ms: number) {
  await new Promise(resolve => setTimeout(resolve, ms));
}
