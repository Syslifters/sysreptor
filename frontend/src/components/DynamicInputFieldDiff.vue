<template>
  <s-card v-if="props.historic.definition?.type === 'object' && props.current.definition?.type === 'object'" class="mt-4" :class="nestedClass">
    <v-card-title class="text-body-1 pb-0">{{ props.historic.definition.label }}</v-card-title>
    <v-card-text>
      <dynamic-input-field-diff 
        v-for="fieldProps in objectFields" 
        :key="fieldProps.id"
        v-bind="fieldProps"
      >
        <template v-for="(_, name) in $slots" #[name]="slotData: any"><slot :name="name" v-bind="slotData" /></template>
      </dynamic-input-field-diff>
    </v-card-text>
  </s-card>
  <s-card v-else-if="props.historic.definition?.type === 'list' && props.current.definition?.type === 'list'" class="mt-4" :class="nestedClass">
    <v-card-title class="text-body-1 pb-0">{{ props.historic.definition.label }}</v-card-title>
    <v-card-text>
      <v-list class="pa-0 bg-inherit">
        <v-list-item v-for="fieldProps in listItemFields" :key="fieldProps.id">
          <dynamic-input-field-diff 
            v-bind="fieldProps" 
          >
            <template v-for="(_, name) in $slots" #[name]="slotData: any"><slot :name="name" v-bind="slotData" /></template>
          </dynamic-input-field-diff>
        </v-list-item>
      </v-list>
    </v-card-text>
  </s-card>
  <markdown-diff-field
    v-else-if="props.historic.definition?.type === 'markdown' && ['markdown', 'string', undefined].includes(props.current.definition?.type)" 
    :label="props.historic.definition.label"
    v-bind="markdownDiffAttrs"
    class="mt-4"
    :class="{'diff-highlight-changed': hasChanged}"
  />
  <v-row v-else>
    <v-col cols="6">
      <dynamic-input-field
        v-if="props.historic.definition"
        v-bind="props.historic"
        :model-value="props.historic.value"
        :definition="props.historic.definition"
        :nesting-level="props.nestingLevel"
        :disabled="!hasChanged"
        :readonly="hasChanged"
        :class="{'diff-highlight-changed': hasChanged}"
      >
        <template v-for="(_, name) in $slots" #[name]="slotData: any"><slot :name="name" v-bind="slotData" /></template>
      </dynamic-input-field>
    </v-col>
    <v-col cols="6">
      <dynamic-input-field 
        v-if="props.current.definition" 
        v-bind="props.current"
        :model-value="props.current.value"
        :definition="props.current.definition"
        :nesting-level="props.nestingLevel"
        :disabled="!hasChanged"
        :readonly="hasChanged"
        :class="{'diff-highlight-changed': hasChanged}"
      >
        <template v-for="(_, name) in $slots" #[name]="slotData: any"><slot :name="name" v-bind="slotData" /></template>
      </dynamic-input-field>
    </v-col>
  </v-row>
</template>

<script setup lang="ts">
import pick from 'lodash/pick';
import merge from 'lodash/merge';
import type { DynamicInputFieldDiffProps } from '~/composables/history';

const props = defineProps<DynamicInputFieldDiffProps>();

const attrs = useAttrs();
const inheritedDiffAttrs = computed(() => {
  const copyFields = [
    'disabled', 'readonly', 'lang', 'spellcheckEnabled', 'markdownEditorMode', 
    'uploadFile', 'rewriteFileUrl', 'rewriteReferenceLink', 'selectableUsers', 
    'onUpdate:markdownEditorMode', 'onUpdate:spellcheckEnabled', 'onCollab',
  ];
  return {
    ...attrs,
    nestingLevel: (props.nestingLevel || 0) + 1,
    historic: pick(props.historic, copyFields),
    current: pick(props.current, copyFields),
  };
});

const objectFields = computed(() => formatHistoryObjectFieldProps({
  historic: {
    value: props.historic.value,
    definition: props.historic.definition?.properties,
    fieldIds: Object.keys(props.historic.definition?.properties || {}).sort(),
    attrs: inheritedDiffAttrs.value.historic,
  },
  current: {
    value: props.current.value,
    definition: props.current.definition?.properties,
    fieldIds: Object.keys(props.current.definition?.properties || {}).sort(),
    attrs: inheritedDiffAttrs.value.current,
  },
  attrs: {
    nestingLevel: inheritedDiffAttrs.value.nestingLevel,
  },
}));
const listItemFields = computed(() => {
  if (props.historic.definition?.type !== 'list') {
    return [];
  }
  const items = [] as DynamicInputFieldDiffProps[];
  for (let i = 0; i < Math.max((props.historic.value || []).length, props.current.definition?.type === 'list' ? (props.current.value || []).length : 0); i++) {
    items.push(merge({
      id: String(i),
      historic: {
        value: props.historic.value?.[i],
        definition: props.historic.definition.items,
      },
      current: {
        value: props.current.value?.[i],
        definition: props.current.definition?.items,
      },
    }, inheritedDiffAttrs.value));
  }
  return items;
});
const markdownDiffAttrs = computed(() => merge({
  disabled: !hasChanged.value,
  readonly: hasChanged.value,
  historic: {
    value: props.historic.value,
  },
  current: {
    value: props.current.value,
  },
}, inheritedDiffAttrs.value));

const hasChanged = computed(() => {
  return props.historic.definition?.type !== props.current.definition?.type || 
    (props.historic.value !== props.current.value && (!!props.historic.value || !!props.current.value));
});

const nestedClass = computed(() => {
  if ([FieldDataType.OBJECT, FieldDataType.LIST].includes(props.historic.definition?.type as any)) {
    return (props.nestingLevel || 0) % 2 === 0 ? 'field-highlight-nested1' : 'field-highlight-nested2';
  }
  return undefined;
})
</script>
