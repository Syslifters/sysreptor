<template>
  <v-hover 
    v-if="[FieldDataType.OBJECT, FieldDataType.LIST].includes(props.current.definition?.type as any) && props.current.definition?.type === props.historic.definition?.type"
    v-model="isHovering"
  >
    <template #default="{ props: hoverProps }">
      <div :id="props.id" class="mt-4" :class="nestedClass" v-bind="hoverProps">
        <s-card v-if="props.current.definition?.type === 'object'">
          <v-card-item class="pb-0">
            <v-card-title class="text-body-1">{{ props.current.definition.label }}</v-card-title>
            <template #append>
              <comment-btn
                v-if="props.current.collab"
                v-bind="commentBtnAttrs"
              />
            </template>
          </v-card-item>
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
        <s-card v-else-if="props.current.definition?.type === 'list'">
          <v-card-item class="pb-0">
            <v-card-title class="text-body-1">{{ props.current.definition.label }}</v-card-title>
            <template #append>
              <comment-btn
                v-if="props.current.collab"
                v-bind="commentBtnAttrs"
              />
            </template>
          </v-card-item>
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
      </div>
    </template>
  </v-hover>
  <div v-else-if="props.historic.definition?.type === FieldDataType.MARKDOWN && props.current.definition?.type === FieldDataType.MARKDOWN" class="mt-4">
    <markdown-diff-field
      :label="props.current.definition.label"
      v-bind="markdownDiffAttrs"
      :class="{'diff-highlight-changed': hasChanged}"
    />
  </div>
  <v-row v-else dense class="mt-0">
    <v-col cols="6">
      <dynamic-input-field
        v-if="props.historic.definition"
        v-bind="omit(props.historic, ['value', 'definition'])"
        :model-value="props.historic.value"
        :definition="props.historic.definition"
        :nesting-level="props.nestingLevel"
        :disabled="true"
        :class="{'diff-highlight-changed': hasChanged}"
      >
        <template v-for="(_, name) in $slots" #[name]="slotData: any"><slot :name="name" v-bind="slotData" /></template>
      </dynamic-input-field>
    </v-col>
    <v-col cols="6">
      <dynamic-input-field 
        v-if="props.current.definition" 
        v-bind="omit(props.current, ['value', 'definition'])"
        :model-value="props.current.value"
        :definition="props.current.definition"
        :nesting-level="props.nestingLevel"
        :readonly="props.current.readonly"
        :id="props.id"
        :class="{'diff-highlight-changed': hasChanged}"
      >
        <template v-for="(_, name) in $slots" #[name]="slotData: any"><slot :name="name" v-bind="slotData" /></template>
      </dynamic-input-field>
    </v-col>
  </v-row>
</template>

<script setup lang="ts">
import { pick, merge, omit } from 'lodash-es';
import type { DynamicInputFieldDiffProps } from '~/composables/history';

const props = defineProps<DynamicInputFieldDiffProps>();

const attrs = useAttrs();
const inheritedDiffAttrs = computed(() => {
  const copyFields = [
    'disabled', 'readonly', 'lang', 'spellcheckEnabled', 'markdownEditorMode', 
    'uploadFile', 'rewriteFileUrl', 'rewriteReferenceLink', 'selectableUsers', 
    'fieldValueSuggestions',
    'onUpdate:markdownEditorMode', 'onUpdate:spellcheckEnabled', 
    'collab', 'onCollab', 'onComment',
  ];
  return {
    ...attrs,
    nestingLevel: (props.nestingLevel || 0) + 1,
    historic: pick(props.historic, copyFields),
    current: pick(props.current, copyFields),
  };
});

const objectFields = computed(() => formatHistoryObjectFieldProps({
  id: props.id,
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
    items.push(merge({}, inheritedDiffAttrs.value, {
      id: `${props.id}[${i}]`,
      historic: {
        value: props.historic.value?.[i],
        definition: props.historic.definition.items,
      },
      current: {
        value: props.current.value?.[i],
        definition: props.current.definition?.items,
        collab: props.current.collab ? collabSubpath(props.current.collab, `[${i}]`) : undefined,
      },
    }));
  }
  return items;
});
const markdownDiffAttrs = computed(() => merge({}, inheritedDiffAttrs.value, {
  id: props.id,
  historic: {
    value: props.historic.value,
  },
  current: {
    value: props.current.value,
  },
}));

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

const isHovering = ref(false);
const commentBtnAttrs = computed(() => ({
  comments: props.current.collab?.comments.filter(c => c.collabPath === props.current.collab?.path) || [],
  onComment: (v: any) => props.current?.onComment?.(v),
  collabPath: props.current.collab?.path || '',
  isHovering: isHovering.value,
  disabled: (props.current as any).disabled || props.current.readonly,
  density: 'comfortable',
}));
</script>
