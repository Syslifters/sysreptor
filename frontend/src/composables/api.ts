import { debounce, isEqual } from "lodash-es";
import { useFetch, useAsyncData } from "nuxt/app";
import type { NuxtApp, AsyncDataOptions } from "nuxt/app";
import type { PaginatedResponse } from "@/utils/types";

export async function useFetchE<T>(...args: Parameters<typeof useFetch<T>>): Promise<Ref<T>> {
  const res = await useFetch(...args);
  if (res.error.value) {
    throw createError({ ...res.error.value, fatal: true });
  }
  return res.data as Ref<T>;
}

export async function useAsyncDataE<T>(handler: (ctx?: NuxtApp) => Promise<T>, options?: AsyncDataOptions<T> & { key?: string }): Promise<Ref<T>> {
  // By default, if no key is provided Nuxt calculates a key based on the current file location of the useAsyncData call.
  // Since we use a wrapper, the key will always be the same. Therefore, set an explicit key derived from arguments.
  const key = options?.key || handler.toString();
  const res = await useAsyncData(key, handler, options);
  if (res.error.value) {
    throw createError({ ...res.error.value, fatal: true });
  }
  return res.data as Ref<T>;
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
  const fetchNextPageDebounced = debounce(async () => {
    await fetcher.value.fetchNextPage();
    initializingFetcher.value = true;
  }, 750);
  function createFetcher(options: { baseURL: string|null, query?: object, fetchInitialPage?: boolean, debounce?: boolean }) {
    const newFetcher = useCursorPaginationFetcher<T>(options) as any;
    if (options.fetchInitialPage) {
      initializingFetcher.value = true;
      if (options.debounce) {
        fetchNextPageDebounced();
      } else {
        fetchNextPage();
      }
    }
    fetcher.value = newFetcher
  }
  createFetcher(options);

  async function fetchNextPage() {
    fetchNextPageDebounced!();
    await fetchNextPageDebounced!.flush();
    initializingFetcher.value = false;
  }

  const currentQuery = computed(() => {
    return Object.fromEntries(new URLSearchParams((fetcher.value.baseURL || '').split('?')[1] || ''));
  });

  function applyFilters(query: object, { fetchInitialPage = true, debounce = false } = {}) {
    const newQuery = { ...currentQuery.value, ...query };
    if (isEqual(currentQuery.value, newQuery)) {
      return;
    }
    createFetcher({ baseURL: fetcher.value.baseURL, query: newQuery, fetchInitialPage, debounce });
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
    currentQuery,
    search,
    applyFilters,
    fetchNextPage,
    fetchNextPageDebounced: fetchNextPageDebounced as () => void,
    reset,
  };
}
