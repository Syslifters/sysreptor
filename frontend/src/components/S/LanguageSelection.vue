<template>
  <s-autocomplete
    :model-value="props.modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    :items="languageInfos"
    item-value="code"
    item-title="name"
    label="Language"
  >
    <template #prepend-inner>
      <v-icon size="small" start icon="mdi-translate" />
    </template>
    <template #item="{item, props: itemProps}">
      <v-list-item :title="item.title" v-bind="itemProps">
        <template #prepend>
          <v-icon size="small" start icon="mdi-translate" />
        </template>
      </v-list-item>
    </template>
  </s-autocomplete>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  modelValue: string|null;
  items?: Language[]|null;
}>(), {
  items: null
});
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()
const initialLanguage = props.modelValue;

const apiSettings = useApiSettings();
const languageInfos = computed(() => props.items || apiSettings.settings!.languages.filter(l => l.enabled || l.code === initialLanguage));
</script>
