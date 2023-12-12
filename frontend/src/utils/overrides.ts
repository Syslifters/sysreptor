import { useHead as useHeadOriginal } from '@unhead/vue';
import type { ReactiveHead } from '@unhead/vue';
import type { Breadcrumbs } from './types';

export function useHeadExtended(options: ReactiveHead & { breadcrumbs?: () => Breadcrumbs }) {
  // Extend useHead to accept more options and prevent TypeScript errors
  return useHeadOriginal(options);
}
