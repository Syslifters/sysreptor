<template>
  <s-combobox
    :model-value="props.modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    :items="tagSuggestions"
    label="Tags"
    multiple
    chips closable-chips
    spellcheck="false"
  >
    <template #chip="{item, props: chipProps}">
      <v-chip size="small" v-bind="chipProps">
        <v-icon size="small" start icon="mdi-tag" class="ml-0" /> {{ item.title }}
      </v-chip>
    </template>
  </s-combobox>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  modelValue: string[];
  items?: string[];
}>(), {
  items: () => ([]),
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
