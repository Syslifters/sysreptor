export function useListSelection<T extends { id: string }>(options: {
  items: MaybeRefOrGetter<T[]>;
  enabled?: MaybeRefOrGetter<boolean>;
}) {
  const items = toRef(options.items);
  const enabled = toRef(options.enabled ?? true);
  const selectedIds = ref<string[]>([]);
  const selectedItems = computed(() => {
    if (!enabled.value) {
      return [];
    }
    return items.value.filter(item => selectedIds.value.includes(item.id));
  });
  const rangeAnchorId = ref<string|null>(null);

  function clearSelection() {
    selectedIds.value = [];
    rangeAnchorId.value = null;
  }
  watch(items, () => clearSelection());

  function selectAll() {
    if (!enabled.value) {
      return;
    }
    selectedIds.value = items.value.map(i => i.id);
    rangeAnchorId.value = selectedItems.value.at(-1)?.id ?? null;
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
        selectedIds.value = selectedIds.value.concat(idsInRange.filter(i => !selectedIds.value.includes(i)));
      } else {
        selectedIds.value = selectedIds.value.filter(i => !idsInRange.includes(i));
      }
    }

    rangeAnchorId.value = event.id;
  }

  const listProps = computed(() => ({
    selected: selectedIds.value,
    'onUpdate:selected': (v: string[]) => { selectedIds.value = v; },
    selectable: enabled.value,
    selectStrategy: 'leaf' as const,
    'onClick:select': onClickSelect,
  }))

  return {
    enabled,
    items,
    selectedItems,
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

