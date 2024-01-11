<template>
  <s-card v-if="props.historic.definition?.type === 'object' && props.current.definition?.type === 'object'" class="mt-4">
    <v-card-title class="text-body-1 pb-0">{{ props.historic.definition.label }}</v-card-title>
    <v-card-text>
      <dynamic-input-field-diff 
        v-for="fieldProps in objectFields" 
        :key="fieldProps.id"
        v-bind="fieldProps"
      />
    </v-card-text>
  </s-card>
  <s-card v-else-if="props.historic.definition?.type === 'list' && props.current.definition?.type === 'list'" class="mt-4">
    <v-card-title class="text-body-1 pb-0">{{ props.historic.definition.label }}</v-card-title>
    <v-card-text>
      <v-list class="pa-0">
        <v-list-item v-for="fieldProps in listItemFields" :key="fieldProps.id">
          <dynamic-input-field-diff 
            v-bind="fieldProps" 
          />
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
        :definition="props.historic.definition"
        :model-value="props.historic.value"
        :disabled="!hasChanged"
        :readonly="hasChanged"
        :class="{'diff-highlight-changed': hasChanged}"
      />
    </v-col>
    <v-col cols="6">
      <dynamic-input-field 
        v-if="props.current.definition" 
        v-bind="props.current"
        :model-value="props.current.value"
        :definition="props.current.definition"
        :disabled="!hasChanged"
        :readonly="hasChanged"
        :class="{'diff-highlight-changed': hasChanged}"
      />
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
  const copyFields = ['selectableUsers', 'onUpdate:markdownEditorMode', 'lang', 'markdownEditorMode', 'rewriteFileUrl', 'rewriteReferenceLink'];
  return {
    ...attrs,
    historic: pick(props.historic, copyFields),
    current: pick(props.current, copyFields),
  };
});

const objectFields = computed(() => formatHistoryObjectFieldProps({
  historic: {
    value: props.historic.value,
    definition: props.historic.definition?.properties,
    fieldIds: Object.keys(props.historic.definition?.properties || {}),
    attrs: inheritedDiffAttrs.value.historic,
  },
  current: {
    value: props.current.value,
    definition: props.current.definition?.properties,
    fieldIds: Object.keys(props.current.definition?.properties || {}),
    attrs: inheritedDiffAttrs.value.current,
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
</script>

<!--
TODO: history diff
* [x] side-by-side markdown diff
  * [x] extensions not applied to B (right side, current)
  * [x] handle lineWrapping with different line lengths => supported by @codemirror/merge
  * [x] side-by-side preview
  * [x] skip markdown_and_preview mode
* [x] indicate changed non-markdown fields: colored border
* [x] nested object, list diff
* [x] handle incompatible definition field types
* [x] handle missing fields
* [x] rewriteFileUrl: historic and current
* [x] history pages: fetch obj+projecttype: historic and current
* [x] show history of deleted finding => do not crash
* [x] useHistory: fetch+error handling instead of useAsyncDataE
* [x] show history of deleted projecttype => do not crash
* [x] markdown-diff-page for notes
* [x] markdown-diff-field: toolbar markdownEditorMode button not visible
* [x] show only used template fields in history
* [ ] feedback
  * [x] side-by-side string field diff => no
  * [x] toggle diff in pages or always use diff => always diff
  * [x] disable unchanged fields, readonly changed fields
  * [ ] remove historic banner; add date to history headline => does not work for notes
  * [ ] finished project: readonly instead of disabled
* [x] rework all history pages
  * [x] findings
  * [x] sections
  * [x] notes
  * [x] templates
* [ ] cleanup
  * [x] move composables to composables/history.ts
  * [x] helper functions for field diffing in composables/history.ts => use in pages and components
  * [ ] fix typescript errors
-->
