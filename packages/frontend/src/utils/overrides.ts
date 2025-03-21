import { useHead } from '#imports'
import type { Breadcrumbs, SyncState } from '@base/utils/types';

export function useHeadExtended(options: Parameters<typeof useHead>[0] & { 
  breadcrumbs?: () => Breadcrumbs;
  syncState?: ComputedRef<SyncState>;
}) {
  // Extend useHead to accept more options and prevent TypeScript errors
  return useHead(options);
}
