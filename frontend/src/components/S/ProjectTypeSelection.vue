<template>
  <s-autocomplete
    :model-value="props.modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    :label="props.label"
    :items="allItems"
    :item-title="formatProjectTypeTitle"
    item-value="id"
    :return-object="props.returnObject"
    :readonly="props.readonly"
    :rules="rules"
    :clearable="!props.required && !props.readonly"
    :hide-no-data="false"
    spellcheck="false"
  >
    <template #append-item v-if="allItems.length > 0">
      <page-loader :items="items" />
    </template>
    <template #no-data v-if="allItems.length === 0 && items.hasNextPage.value">
      <page-loader :items="items" />
    </template>
    <template #item="{item: { raw: projectType}, props: itemProps}">
      <design-list-item :item="projectType" :format-title="true" :to="null" lines="one" v-bind="itemProps" />
    </template>
    <template #append v-if="appendLink">
      <s-btn-icon
        :to="`/designs/${returnObject ? (props.modelValue as ProjectType|null)?.id : props.modelValue}/pdfdesigner/`"
        target="_blank"
        :disabled="!props.modelValue"
        class="mr-2"
      >
        <v-icon icon="mdi-chevron-right-circle-outline" />
        <s-tooltip activator="parent" text="Open Design" />
      </s-btn-icon>
    </template>
    <template #message="messageProps" v-if="$slots.message"><slot name="message" v-bind="messageProps" /></template>
  </s-autocomplete>
</template>

<script setup lang="ts">
import { isObject } from "lodash-es";

const props = withDefaults(defineProps<{
  modelValue: ProjectType|string|null,
  returnObject?: boolean,
  required?: boolean,
  readonly?: boolean,
  additionalItems?: ProjectType[],
  queryFilters?: Object,
  appendLink?: boolean,
  label?: string,
}>(), {
  returnObject: false,
  required: false,
  readonly: false,
  additionalItems: () => [],
  queryFilters: () => ({}),
  appendLink: false,
  label: 'Design',
});
const emit = defineEmits<{
  (e: 'update:modelValue', value: ProjectType|string|null): void,
}>();

const items = useSearchableCursorPaginationFetcher<ProjectType>({
  baseURL: '/api/v1/projecttypes/',
  query: {
    ordering: 'status,scope,name,-created',
    scope: [ProjectTypeScope.GLOBAL, ProjectTypeScope.PRIVATE],
    ...props.queryFilters
  }
});

const rules = [
  (v: any) => !props.required || Boolean(v) || 'Item is required',
]

const projectTypeStore = useProjectTypeStore();
const initialProjectType = ref<ProjectType|null>(null);
useLazyAsyncData(async () => {
  if (props.modelValue && !props.additionalItems.some(pt => [props.modelValue, (props.modelValue as any)?.id].includes(pt.id))) {
    if (isObject(props.modelValue)) {
      initialProjectType.value = props.modelValue;
    } else {
      try {
        initialProjectType.value = await projectTypeStore.getById(props.modelValue as string);
      } catch (error: any) {
        if (error?.status === 404) {
          initialProjectType.value = null;
          emit('update:modelValue', null);
        }
      }
      if (props.returnObject) {
        emit('update:modelValue', initialProjectType.value);
      }
    }
  } else if (props.modelValue && props.returnObject && !isObject(props.modelValue)) {
    initialProjectType.value = props.additionalItems.find(pt => pt.id === props.modelValue) || null;
    if (initialProjectType.value) {
      emit('update:modelValue', initialProjectType.value);
    }
  }
});

const allItems = computed(() => {
  const out = props.additionalItems.concat(items.data.value);
  if (initialProjectType.value && !out.some(pt => pt.id === initialProjectType.value?.id)) {
    out.push(initialProjectType.value);
  }
  return out;
})
</script>

<style lang="scss" scoped>
:deep() {
  .v-field__input input {
    flex: 1 1;
    position: absolute;
  }
}
</style>
