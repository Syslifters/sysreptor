import { ref } from 'vue';

const PINNED_FILTERS_KEY = 'pinnedFilters';

export function usePinnedFilters() {
  function getPinnedFilters(): string[] {
    try {
      const p = JSON.parse(localStorage.getItem(PINNED_FILTERS_KEY) || '[]');
      console.debug('[usePinnedFilters] getPinnedFilters', p);
      return p;
    } catch {
      return [];
    }
  }

  function setPinnedFilters(filters: string[]) {
    localStorage.setItem(PINNED_FILTERS_KEY, JSON.stringify(filters));
    console.debug('[usePinnedFilters] setPinnedFilters', filters);
  }

  function pinFilter(id: string) {
    const pinned = getPinnedFilters();
    if (!pinned.includes(id)) {
      pinned.push(id);
      setPinnedFilters(pinned);
    }
  }

  function unpinFilter(id: string) {
    const before = getPinnedFilters();
    const after = before.filter(f => f !== id);
    setPinnedFilters(after);
    console.debug('[usePinnedFilters] unpinFilter', { id, before, after });
  }

  function isPinned(id: string): boolean {
    return getPinnedFilters().includes(id);
  }

  function restorePinnedFilters(filterProperties: any[]): any[] {
    const pinned = getPinnedFilters();
    const restored: any[] = [];
    for (const filterProp of filterProperties) {
      for (const pin of pinned) {
        if (pin.startsWith(filterProp.name + ':')) {
          let value;
          try {
            value = JSON.parse(pin.slice(filterProp.name.length + 1));
          } catch { value = undefined; }
          restored.push({ id: filterProp.id, value, exclude: false });
        }
      }
    }
    console.debug('[usePinnedFilters] restorePinnedFilters', { filterProperties, pinned, restored });
    return restored;
  }

  return {
    getPinnedFilters,
    setPinnedFilters,
    pinFilter,
    unpinFilter,
    isPinned,
    restorePinnedFilters,
  };
}
