<template>
  <s-input v-model="modelValue" class="v-text-field" v-bind="$attrs">
    <template #default="{id, isDirty, isDisabled, isReadonly, isValid }">
      <s-field
        v-bind="$attrs"
        v-model:focused="isFocused"
        :id="id.value"
        :dirty="isDirty.value"
        :active="isDirty.value || isFocused"
        :disabled="isDisabled.value"
        :readonly="isReadonly.value"
        :error="isValid.value === false"
        @click="onControlClick"
      >
        <template #label v-if="$slots.label"><slot name="label" /></template>
        <template #default="{ props: fieldProps, focus, blur }">
          <comment-text-field-content
            ref="contentRef"
            v-model="modelValue"
            v-bind="{ ...props, ...$attrs, ...fieldProps }"
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
const modelValue = defineModel<string|null>();
const props = defineProps<{
  selectableUsers?: UserShortInfo[];
}>();

const contentRef = useTemplateRef('contentRef');
const isFocused = ref(false);
function onControlClick() {
  contentRef.value?.focus();
}

const attrs = useAttrs();
function onIntersect() {
  if (attrs.autofocus && !attrs.disabled) {
    contentRef.value?.focus();
  }
}
</script>
