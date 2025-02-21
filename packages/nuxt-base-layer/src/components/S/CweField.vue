<template>
  <s-autocomplete
    :model-value="props.modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    @focus="emit('focus', $event)"
    @blur="emit('blur', $event)"
    :items="items"
    :item-title="cweTitle"
    :custom-filter="filterCweItem"
    :clearable="true"
    spellcheck="false"
  >
    <template #label v-if="$slots.label"><slot name="label" /></template>
    <template #item="{ item: { raw: cwe }, props: itemProps}">
      <v-list-item v-bind="itemProps" density="compact">
        <template #prepend>
          <span v-for="i in cwe.level" :key="i" class="tree-level" />
          <v-icon v-if="cwe.hasChildren" icon="mdi-menu-down" />
          <v-icon v-else :icon="undefined" />
        </template>
        <template #default>
          <s-tooltip 
            activator="parent" 
            location="top" 
            open-delay="1000"
            :text="cwe.description" 
          />
        </template>
      </v-list-item>
    </template>
  </s-autocomplete>
</template>

<script setup lang="ts">
import { sortBy } from 'lodash-es';

const props = defineProps<{
  modelValue?: string|null;
  readonly?: boolean;
  disabled?: boolean;
}>();
const emit = defineEmits<{
  'update:modelValue': [value: string|null];
  'focus': [e: FocusEvent];
  'blur': [e: FocusEvent];
}>();

const apiSettings = useApiSettings();
useLazyAsyncData(async () => {
  await apiSettings.getCwes();
});

type CWEItem = CWE & {
  level: number;
  value: string;
  hasChildren: boolean;
  children: CWEItem[];
}
const items = computed(() => {
  const cwes = sortBy((apiSettings.cwes || []), ['id']);

  function collectChildren(parentId: number|null, level: number): CWEItem[] {
    return cwes
      .filter(c => c.parent === parentId)
      .flatMap((c) => {
        const children = collectChildren(c.id, level + 1);
        const cweItem = {
          ...c,
          value: `CWE-${c.id}`,
          level,
          hasChildren: children.length > 0,
          children,
        };
        return [cweItem].concat(children);
      });
  }
  return collectChildren(null, 0);
});

function cweTitle(item: CWEItem) {
  return `${item.value} - ${item.name}`; 
}

function filterCweItem(_value: string, query: string, item: { raw: CWEItem }) {
  // Include matching items and their parents
  const queryWords = query.toLocaleLowerCase().split(' ');

  function matches(cwe: CWEItem): boolean|number[][] {
    const searchValue = cweTitle(cwe).toLocaleLowerCase();
    const searchResults = queryWords
      .map((q) => {
        const resultIdx = searchValue.indexOf(q);
        return [resultIdx, resultIdx + q.length];
      })
      .filter(r => r[0]! >= 0);
    if (searchResults.length === queryWords.length) {
      return searchResults;
    } else {
      return cwe.children.some(c => matches(c));
    }
  }
  return matches(item.raw);
}
</script>

<style scoped lang="scss">
.tree-level {
  margin-left: 1em;
}

:deep(.v-list-item__prepend) {
  .v-list-item__spacer {
    width: 0.5em;
  }
}
</style>
