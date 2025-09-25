<template>
  <s-combobox
    :model-value="props.modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    :items="tagSuggestions"
    :readonly="props.readonly"
    label="Tags"
    multiple
    chips 
    :hide-no-data="false"
    :closable-chips="!props.readonly"
    spellcheck="false"
  >
    <template #chip="{item, props: chipProps}">
      <v-chip size="small" v-bind="chipProps">
        <v-icon size="small" start icon="mdi-tag" class="ml-0" /> {{ item.title }}
      </v-chip>
    </template>
    <template #no-data>
      <span v-intersect="onIntersect" />
    </template>
    <template #append-item>
      <v-list-item
        title="Type to add custom tags..."
        subtitle="Apply with [enter]"
      />
    </template>
  </s-combobox>
</template>

<script setup lang="ts">
import { uniq } from 'lodash-es';

const props = withDefaults(defineProps<{
  modelValue: string[];
  items?: string[]|(() => Promise<string[]>);
  readonly?: boolean;
}>(), {
  items: () => ([]),
  readonly: false,
});
const emit = defineEmits<{
  (e: 'update:modelValue', value: string[]): void
}>();

const tagSuggestions = ref<string[]>([]);
function addTagSuggestions(tags: string[]) {
  tagSuggestions.value = uniq(tagSuggestions.value.concat(tags));
}

async function onIntersect() {
  addTagSuggestions(props.modelValue);

  if (Array.isArray(props.items)) {
    addTagSuggestions(props.items);
  } else if (typeof props.items === 'function') {
    const items = await props.items();
    addTagSuggestions(items);
  }
}

</script>
