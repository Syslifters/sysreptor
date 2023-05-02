import urlJoin from 'url-join';
import { debounce } from 'lodash';

export function absoluteApiUrl(url, axios) {
  if (['http', 'data'].some(p => url.startsWith(p))) {
    return url;
  } else if (url.startsWith('/api/')) {
    return urlJoin(new URL(axios.defaults.baseURL, window.location).origin, url);
  } else {
    return urlJoin(axios.defaults.baseURL, url);
  }
}

export function relativeTo(url, baseUrl) {
  const absUrl = absoluteApiUrl(url);
  baseUrl = absoluteApiUrl(baseUrl);

  if (absUrl.startsWith(baseUrl)) {
    return absUrl.substring(baseUrl.length);
  } else {
    return url;
  }
}

export class CursorPaginationFetcher {
  constructor(baseURL, axios, toast) {
    this.axios = axios;
    this.toast = toast;
    this.baseURL = baseURL;

    this.nextPageURL = this.baseURL;
    this.isLoading = false;
    this.data = [];
    this.hasError = false;
    this.errorData = null;
  }

  get hasNextPage() {
    return this.nextPageURL !== null;
  }

  async fetchNextPage() {
    if (!this || this.isLoading || !this.hasNextPage) {
      return;
    }

    try {
      this.isLoading = true;

      const res = await this.axios.$get(this.nextPageURL);
      this.nextPageURL = res.next;
      this.data.push(...res.results);

      this.hasError = false;
      this.errorData = null;
    } catch (error) {
      this.hasError = true;
      this.errorData = error?.response?.data || null;

      this.toast.global.requestError({ error });
    } finally {
      this.isLoading = false;
    }
  }
}

export class SearchableCursorPaginationFetcher {
  constructor({ baseURL, searchFilters = { search: '' }, axios, toast }) {
    this.axios = axios;
    this.toast = toast;
    this.baseURL = baseURL;
    this._searchFilters = searchFilters;

    this._fetchNextPageDebounced = debounce(function() { this._fetchNextPage(); }, 500);

    this.fetcher = null;
    this._createFetcher();
  }

  _createFetcher() {
    const searchParams = new URLSearchParams(this.baseURL.split('?')[1]);
    for (const [k, v] of Object.entries(this.searchFilters)) {
      if (v) {
        if (Array.isArray(v)) {
          searchParams.delete(k);
          for (const e of v) {
            searchParams.append(k, e);
          }
        } else {
          searchParams.set(k, v);
        }
      }
    }
    const searchUrl = this.baseURL.split('?')[0] + '?' + searchParams.toString();
    this.fetcher = new CursorPaginationFetcher(searchUrl, this.axios, this.toast);
  }

  search(val) {
    this._searchFilters = Object.assign(this._searchFilters, { search: val })
    this._createFetcher();
    this.fetchNextPage();
  }

  applyFilters(filters) {
    Object.assign(this._searchFilters, filters);
    this._createFetcher();
    this.fetchNextPageImmediate()
  }

  get searchFilters() {
    return this._searchFilters;
  }

  get searchQuery() {
    return this.searchFilters.search;
  }

  set searchQuery(val) {
    this.search(val, this._searchFilters);
  }

  get hasNextPage() {
    return this.fetcher.hasNextPage;
  }

  get hasError() {
    return this.fetcher.hasError;
  }

  get errorData() {
    return this.fetcher.errorData;
  }

  get data() {
    return this.fetcher.data;
  }

  fetchNextPage() {
    this._fetchNextPageDebounced();
  }

  async _fetchNextPage() {
    await this.fetcher.fetchNextPage();
  }

  fetchNextPageImmediate() {
    if (!this) {
      return;
    }

    this._fetchNextPageDebounced();
    this._fetchNextPageDebounced.flush();
  }
}
