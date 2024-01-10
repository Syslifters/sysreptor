<template>
  <s-card v-if="props.historic.definition?.type === 'object' && props.current.definition?.type === 'object'" class="mt-4">
    <v-card-title class="text-body-1 pb-0">{{ props.historic.definition.label }}</v-card-title>
    <v-card-text>
      <dynamic-input-field-diff 
        v-for="fieldProps in objectFields" 
        :key="fieldProps.id"
        v-bind="fieldProps"
      />>
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
    :class="{'highlight-changed': hasChanged}"
  />
  <v-row v-else>
    <v-col cols="6">
      <dynamic-input-field
        v-if="props.historic.definition"
        :model-value="props.historic.value"
        :disabled="true"
        v-bind="props.historic"
        :class="{'highlight-changed': hasChanged}"
      />
    </v-col>
    <v-col cols="6">
      <dynamic-input-field 
        v-if="props.current.definition" 
        :model-value="props.current.value"
        :disabled="true"
        v-bind="props.current"
        :class="{'highlight-changed': hasChanged}"
      />
    </v-col>
  </v-row>
</template>

<script setup lang="ts">
import pick from 'lodash/pick';
import merge from 'lodash/merge';

export type Props = {
  id: string;
  historic: DiffFieldProps;
  current: DiffFieldProps;
}

const props = defineProps<Props>();

const attrs = useAttrs();
const inheritedDiffAttrs = computed(() => {
  const copyFields = ['selectableUsers', 'onUpdate:markdownEditorMode', 'lang', 'markdownEditorMode', 'rewriteFileUrl', 'rewriteReferenceLink'];
  return {
    ...attrs,
    historic: pick(props.historic, copyFields),
    current: pick(props.current, copyFields),
  };
});

const objectFields = computed(() => {
  if (props.historic.definition?.type !== 'object') {
    return [];
  }
  const fields = Object.entries(props.historic.definition.properties!)
    .map(([id, def]) => merge({
      id,
      historic: {
        value: props.historic.value?.[id],
        definition: def,
      },
      current: {
        value: props.current.value?.[id],
        definition: props.current.definition?.properties?.[id],
      },
    }, inheritedDiffAttrs.value)) as Props[];
  fields.push(...Object.entries(props.current.definition?.properties || {})
    .filter(([id, _def]) => !(id in (props.historic.definition?.properties || {})))
    .map(([id, def]) => merge({
      id,
      historic: {
        value: undefined,
        definition: undefined,
      },
      current: {
        value: props.current.value?.[id],
        definition: def,
      },
    }, inheritedDiffAttrs.value)));
  return fields;
});
const listItemFields = computed(() => {
  if (props.historic.definition?.type !== 'list') {
    return [];
  }
  const items = [] as Props[];
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
  historic: {
    value: props.historic.value,
  },
  current: {
    value: props.current.value,
  },
}, inheritedDiffAttrs.value));

const hasChanged = computed(() => {
  return props.historic.definition?.type !== props.current.definition?.type || 
    (props.historic.value !== props.current.value && (props.historic.value || props.current.value));
});
</script>

<style lang="scss" scoped>
.highlight-changed:deep() {
  .v-field.v-field--variant-outlined {
    .v-field__outline {
      --v-field-border-width: 2px;
    }

    .v-field__outline__start, .v-field__outline__end, .v-field__outline__notch::before .v-field__outline__notch::after {
      border-color: rgb(var(--v-theme-info));
    }
  }
}
</style>

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
* [ ] show history of deleted projecttype => do not crash
* [ ] useHistory: fetch+error handling instead of useAsyncDataE
* [ ] toggle diff in pages or always use diff ???
* [ ] DynamicInputFieldDiff: readonly vs disabled?
* [ ] cleanup
  * [x] move composables to composables/history.ts
  * [ ] helper functions for field diffing in composables/history.ts => use in pages and components
* [ ] rework all history pages
  * [ ] findings
  * [ ] sections
  * [ ] notes
  * [ ] templates
-->
