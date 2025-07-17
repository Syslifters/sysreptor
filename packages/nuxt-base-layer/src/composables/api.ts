import { debounce, isEqual } from "lodash-es";
import type { PaginatedResponse } from "#imports";

export async function useAsyncDataE<T>(handler: () => Promise<T>, options?: { deep?: boolean }): Promise<Ref<T>> {
  const nuxtApp = useNuxtApp();
  const createRef: (d: T) => Ref<T> = options?.deep ? ref : shallowRef;
  const dataRef = createRef(null as any);

  async function runHandler() {
    try {
      dataRef.value = await handler();
    } catch (error: any) {
      error.fatal = true;
      throw createError(error);
    }
  }

  const unsubscribeDataRefreshHook = nuxtApp.hook('app:data:refresh', runHandler);
  onScopeDispose(() => {
    unsubscribeDataRefreshHook();
  });

  await runHandler();
  return dataRef;
}

export async function useFetchE<T>(url: string, options: Parameters<typeof $fetch<T>>[1] & { deep?: boolean }): Promise<Ref<T>> {
  return useAsyncDataE(() => $fetch(url, options), options);
}

export function useCursorPaginationFetcher<T>({ baseURL, query }: { baseURL: string|null, query?: object }) {
  const searchParams = new URLSearchParams((baseURL || '').split('?')[1]);
  for (const [k, v] of Object.entries(query || {})) {
    if (v) {
      if (Array.isArray(v)) {
        searchParams.delete(k);
        for (const e of v) {
          searchParams.append(k, e);
        }
      } else {
        searchParams.set(k, v);
      }
    } else {
      searchParams.delete(k);
    }
  }
  if (baseURL) {
    baseURL = baseURL.split('?')[0] + '?' + searchParams.toString();
  }

  const hasBaseURL = computed(() => !!baseURL);
  const nextPageURL = ref<string|null>(baseURL);
  const hasNextPage = computed(() => !!nextPageURL.value);
  const pending = ref(false);
  const data = ref<T[]>([]);
  const error = ref<any|null>(null);
  const hasError = computed(() => error.value !== null);

  async function fetchNextPage() {
    if (pending.value || !hasNextPage.value) {
      return Promise.resolve();
    }

    try {
      pending.value = true;

      const res = await $fetch<PaginatedResponse<T>>(nextPageURL.value!, { method: 'GET' });
      nextPageURL.value = res.next;
      data.value.push(...toRef(res.results).value);
      error.value = null;
    } catch (err: any) {
      error.value = err?.data || 'Could not load data';
      requestErrorToast({ error: err });
    } finally {
      pending.value = false;
    }
  }

  return {
    baseURL,
    data,
    error,
    pending,
    hasError,
    hasNextPage,
    hasBaseURL,
    fetchNextPage,
  };
}

export function useSearchableCursorPaginationFetcher<T>(options: { baseURL: string|null, query?: object }) {
  const initializingFetcher = ref(false);
  const fetcher = ref<ReturnType<typeof useCursorPaginationFetcher<T>>>(null as any);
  const fetcherOptions = ref(options);
  const fetchNextPageDebounced = debounce(async () => {
    await fetcher.value.fetchNextPage();
    initializingFetcher.value = true;
  }, 750);
  function createFetcher(newOptions: { baseURL: string|null, query?: object, fetchInitialPage?: boolean, debounce?: boolean }) {
    const newFetcher = useCursorPaginationFetcher<T>(newOptions) as any;
    if (newOptions.fetchInitialPage) {
      initializingFetcher.value = true;
      if (newOptions.debounce) {
        fetchNextPageDebounced();
      } else {
        fetchNextPage();
      }
    }
    fetcher.value = newFetcher
    fetcherOptions.value = newOptions;
  }
  createFetcher(fetcherOptions.value);

  async function fetchNextPage() {
    fetchNextPageDebounced!();
    await fetchNextPageDebounced!.flush();
    initializingFetcher.value = false;
  }

  const baseURLQuery = Object.fromEntries(new URLSearchParams((fetcherOptions.value.baseURL || '').split('?')[1] || ''));
  const currentQuery = computed(() => {
    return { ...baseURLQuery, ...fetcherOptions.value.query };
  });

  function applyFilters(query: object, { fetchInitialPage = true, debounce = false } = {}) {
    const newQuery = {
      ...baseURLQuery,
      ...query,
    };
    if (isEqual(baseURLQuery.value, newQuery)) {
      return;
    }
    createFetcher({ baseURL: options.baseURL, query: newQuery, fetchInitialPage, debounce });
  }

  const search = computed({
    get: () => currentQuery.value.search || '',
    set: (val: string) => applyFilters({ search: val }, { debounce: true }),
  });

  function reset(opts?: { baseURL: string|null, query?: object }) {
    createFetcher(opts || options);
  }

  return {
    data: computed({
      get: () => fetcher.value.data,
      set: (val) => { fetcher.value.data = val; },
    }),
    error: computed(() => fetcher.value.error),
    pending: computed(() => initializingFetcher.value || fetcher.value.pending),
    hasError: computed(() => fetcher.value.hasError),
    hasNextPage: computed(() => fetcher.value.hasNextPage),
    hasBaseURL: computed(() => fetcher.value.hasBaseURL),
    search,
    applyFilters,
    fetchNextPage,
    fetchNextPageDebounced: fetchNextPageDebounced as () => void,
    reset,
  };
}
