import type { MaybeRefOrGetter } from 'vue';
import type { Breadcrumbs, SyncState } from '@base/utils/types';

type AppBarContribution = {
  breadcrumbs?: MaybeRefOrGetter<Breadcrumbs>;
  syncState?: MaybeRefOrGetter<SyncState | undefined>;
};

const stack = shallowRef<AppBarContribution[]>([]);

export function useAppBar(options?: {
  breadcrumbs?: MaybeRefOrGetter<Breadcrumbs>;
  syncState?: MaybeRefOrGetter<SyncState | undefined>;
}) {
  if (options && (options.breadcrumbs !== undefined || options.syncState !== undefined)) {
    const entry: AppBarContribution = {};
    if (options.breadcrumbs !== undefined) {
      entry.breadcrumbs = options.breadcrumbs;
    }
    if (options.syncState !== undefined) {
      entry.syncState = options.syncState;
    }

    stack.value = [...stack.value, entry];
    onScopeDispose(() => {
      stack.value = stack.value.filter(e => e !== entry);
    });

    if (entry.breadcrumbs !== undefined) {
      // titleTemplate closes over the same reactive deps but is not tracked by unhead;
      // invalidate so document title stays in sync when breadcrumb sources change.
      watchEffect(() => {
        toValue(entry.breadcrumbs);
        injectHead().invalidate?.();
      });
    }
  }

  const breadcrumbs = computed(() => {
    for (let i = stack.value.length - 1; i >= 0; i--) {
      const source = stack.value[i]?.breadcrumbs;
      if (source === undefined) {
        continue;
      }
      return [
        { icon: 'mdi-home', to: '/' },
        ...toValue(source).map(b => ({ ...b, title: b.title || '...', disabled: false })),
      ] as Breadcrumbs;
    }
    return undefined;
  });

  const syncState = computed(() => {
    for (let i = stack.value.length - 1; i >= 0; i--) {
      const source = stack.value[i]?.syncState;
      if (source !== undefined) {
        return toValue(source);
      }
    }
    return undefined;
  });

  return { breadcrumbs, syncState };
}
