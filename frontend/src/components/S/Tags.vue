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
    <template #no-data><span /></template>
    <template #append-item>
      <v-list-item
        title="Type to add custom tags..."
        subtitle="Apply with [enter]"
      />
    </template>
  </s-combobox>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  modelValue: string[];
  items?: string[];
  readonly?: boolean;
}>(), {
  items: () => ([]),
  readonly: false,
});
const emit = defineEmits<{
  (e: 'update:modelValue', value: string[]): void
}>();

const tagSuggestions = ref([...props.items, ...props.modelValue]);
watch(() => props.modelValue, (val) => {
  for (const tag of val) {
    if (!tagSuggestions.value.includes(tag)) {
      tagSuggestions.value.push(tag);
    }
  }
});
</script>
