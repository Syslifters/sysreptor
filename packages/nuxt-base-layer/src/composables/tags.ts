import { useSingletonFetcher } from '@base/composables/api';
import { uniq } from 'lodash-es';

export function useTagsFetcher(url: string) {
  const fetcher = useSingletonFetcher<{ tags: string[] }>(url);

  return {
    tags: computed(() => fetcher.data.value?.tags || []),
    getTags: async () => (await fetcher.getData()).tags,
  };
}

export function useProjectTypeTags() {
  return useTagsFetcher('/api/v1/projecttypes/tags/');
}

export function useFindingTemplateTags() {
  const fetcher = useTagsFetcher('/api/v1/findingtemplates/tags/');
  const builtinTags = [
    'web', 'infrastructure', 'organizational', 'hardening', 'internal', 'external', 'third_party',
    'active_directory', 'windows', 'client',
    'config', 'update', 'development', 'crypto',
  ];

  const tags = computed(() => uniq(fetcher.tags.value.concat(builtinTags)));
  async function getTags() {
    await fetcher.getTags();
    return tags.value;
  }

  return {
    tags,
    getTags,
  };
}

export function useProjectTags() {
  return useTagsFetcher('/api/v1/pentestprojects/tags/');
}

export function useArchivedProjectTags() {
  return useTagsFetcher('/api/v1/archivedprojects/tags/');
}
