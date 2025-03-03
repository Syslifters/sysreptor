import { useHead as useHeadOriginal } from '@unhead/vue';
import type { ReactiveHead } from '@unhead/vue';
import type { Breadcrumbs, SyncState } from '@base/utils/types';

export function useHeadExtended(options: ReactiveHead & { 
  breadcrumbs?: () => Breadcrumbs;
  syncState?: ComputedRef<SyncState>;
}) {
  // Extend useHead to accept more options and prevent TypeScript errors
  return useHeadOriginal(options);
}
