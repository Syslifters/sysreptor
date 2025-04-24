<template>
  <s-input class="v-text-field" v-bind="$attrs">
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
          <markdown-text-field-content
            ref="markdownRef"
            v-bind="{ ...$attrs, ...fieldProps }"
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
const markdownRef = useTemplateRef('markdownRef');
const isFocused = ref(false);
function onControlClick() {
  markdownRef.value?.focus();
}

const attrs = useAttrs();
function onIntersect() {
  if (attrs.autofocus && !attrs.disabled) {
    markdownRef.value?.focus();
  }
}
</script>
