import { uniq } from "lodash-es";

export function useListSelection<T extends { id: string }>(options: {
  items: MaybeRefOrGetter<T[]>;
  enabled?: MaybeRefOrGetter<boolean>;
}) {
  const items = computed<T[]>(() => toValue(options.items) as T[]);
  const enabled = computed<boolean>(() => toValue(options.enabled ?? true) as boolean);
  const selectedIdsAll = ref<string[]>([]);
  
  const itemById = shallowRef(new Map<string, T>());
  watch(items, () => {
    const newItemById = new Map<string, T>(itemById.value);
    items.value.forEach(i => newItemById.set(i.id, i));
    itemById.value = newItemById;
  }, { deep: 1, immediate: true });

  const visibleIds = computed(() => items.value.map(i => i.id));
  const selectedIdsVisible = computed(() => {
    if (!enabled.value) {
      return [];
    }
    const visibleSet = new Set(visibleIds.value);
    return selectedIdsAll.value.filter(id => visibleSet.has(id));
  });
  const selectedItems = computed(() => {
    if (!enabled.value) {
      return [];
    }
    return selectedIdsAll.value
      .map(id => itemById.value.get(id))
      .filter((item): item is T => Boolean(item));
  });
  const selectedItemsVisible = computed(() => selectedItems.value.filter(item => visibleIds.value.includes(item.id)));
  
  const rangeAnchorId = ref<string|null>(null);
  function clearSelection() {
    selectedIdsAll.value = selectedIdsAll.value.filter(id => !visibleIds.value.includes(id));
    rangeAnchorId.value = null;
  }
  function selectAll() {
    if (!enabled.value) {
      return;
    }
    selectedIdsAll.value = uniq([...selectedIdsAll.value, ...visibleIds.value]);;
    rangeAnchorId.value = visibleIds.value.at(-1) ?? null;
  }

  const shiftKey = useKeyModifier('Shift');
  async function onClickSelect(event: { id: any, value: boolean }) {
    // Handle range selection
    // Regular selection is handled by vuetify
    if (shiftKey.value) {
      const anchorIndex = items.value.findIndex(i => i.id === rangeAnchorId.value);
      const targetIndex = items.value.findIndex(i => i.id === event.id);
      if (anchorIndex < 0 || targetIndex < 0) {
        return;
      }
      const idsInRange = items.value
        .slice(Math.min(anchorIndex, targetIndex), Math.max(anchorIndex, targetIndex) + 1)
        .map(i => i.id);
      
      await nextTick();
      if (event.value) {
        selectedIdsAll.value = uniq([...selectedIdsAll.value, ...idsInRange]);
      } else {
        selectedIdsAll.value = selectedIdsAll.value.filter(i => !idsInRange.includes(i));
      }
    }

    rangeAnchorId.value = event.id;
  }

  const listProps = computed(() => ({
    selected: selectedIdsVisible.value,
    'onUpdate:selected': (value: string[]) => {
      const prevVisible = selectedIdsVisible.value;

      const removedFromVisible = prevVisible.filter(id => !value.includes(id));
      const kept = selectedIdsAll.value.filter(id => !removedFromVisible.includes(id));
      const added = value.filter(id => !kept.includes(id));

      selectedIdsAll.value = uniq([...kept, ...added]);
    },
    selectable: enabled.value,
    selectStrategy: 'leaf' as const,
    'onClick:select': onClickSelect,
  }));

  return {
    enabled,
    items,
    selectedItems,
    selectedItemsVisible,
    clearSelection,
    selectAll,
    listProps,
  };
}


export async function bulkAction<T>(
  items: T[],
  actionForItem: (item: T) => Promise<void> | void,
  formatErrorMessage?: (item: T) => string,
) {
  const deleteTasks = items.map(async (item) => {
    try {
      await Promise.resolve(actionForItem(item));
    } catch (error: any) {
      if (error?.status === 404) {
        // Item was already deleted (or not found): ignore.
        return;
      }
      requestErrorToast({ error, message: formatErrorMessage?.(item) });
    }
  });

  await Promise.all(deleteTasks);
}

