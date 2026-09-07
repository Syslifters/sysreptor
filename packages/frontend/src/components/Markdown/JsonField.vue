<template>
  <s-input
    ref="inputRef"
    v-model="modelValue"
    class="v-text-field"
    :rules="[validateJsonRule]"
    validate-on="input lazy"
    v-bind="$attrs"
  >
    <template #default="{ id, isDirty, isDisabled, isReadonly, isValid }">
      <s-field
        v-bind="$attrs"
        v-model:focused="isFocused"
        :id="id.value"
        :dirty="isDirty.value"
        :active="true"
        :disabled="isDisabled.value"
        :readonly="isReadonly.value"
        :error="isValid.value === false"
        @click="onControlClick"
      >
        <template #label v-if="$slots.label"><slot name="label" /></template>
        <template #default="{ props: fieldProps, focus, blur }">
          <markdown-json-field-content
            ref="editorRef"
            v-model="modelValue"
            :schema="props.schema"
            v-bind="{ ...markdownProps, ...$attrs, ...fieldProps }"
            @focus="focus()"
            @blur="blur()"
            v-intersect.once="onIntersect"
          />
        </template>
      </s-field>
    </template>
  </s-input>
</template>

<script setup lang="ts">
import { debounce } from 'lodash-es';
import ZSchema from 'z-schema';
import type { MarkdownProps } from '@/composables/markdown';

defineOptions({
  inheritAttrs: false,
});

const modelValue = defineModel<string|null>();
const props = defineProps<MarkdownProps & {
  schema?: Record<string, any>|null;
}>();

const editorRef = useTemplateRef('editorRef');
const inputRef = useTemplateRef<{ validate: () => Promise<{ valid: boolean }> }|null>('inputRef');
const isFocused = ref(false);

const markdownProps = computed(() => {
  const { schema: _schema, ...rest } = props;
  return rest;
});

const validator = ZSchema.create({ safe: true });
const validationResult = ref<true|string>(true);

function computeValidation(value: string|null|undefined): true|string {
  if (!value) {
    return true;
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(value);
  } catch (e: any) {
    return `Invalid JSON: ${e.message}`;
  }

  if (props.schema) {
    const result = validator.validate(parsed, props.schema);
    if (!result.valid) {
      const msg = result.err?.details?.[0]?.message;
      return msg ? 
        `Invalid data: JSON schema: ${msg}` : 
        'Invalid data: JSON schema';
    }
  }

  return true;
}

const runValidation = debounce((value: string|null|undefined) => {
  validationResult.value = computeValidation(value);
  inputRef.value?.validate();
}, 1000);

watch(modelValue, (value) => {
  runValidation(value);
}, { immediate: true });

watch(() => props.schema, () => {
  runValidation(modelValue.value);
});

function validateJsonRule(_value: string|null) {
  return validationResult.value;
}

function onControlClick() {
  editorRef.value?.focus();
}

const attrs = useAttrs();
function onIntersect() {
  if (attrs.autofocus && !attrs.disabled) {
    editorRef.value?.focus();
  }
}

onBeforeUnmount(() => {
  runValidation.cancel();
});
</script>

<style lang="scss" scoped>
.v-field__input {
  padding: 0 1px;
  cursor: initial;
  row-gap: 0;
}
</style>
