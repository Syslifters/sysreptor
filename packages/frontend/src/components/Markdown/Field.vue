<template>
  <s-input class="v-text-field" v-bind="$attrs">
    <template #default="{id, isDirty, isDisabled, isReadonly, isValid }">
      <s-field
        v-bind="$attrs"
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
          <markdown-field-content
            ref="markdownRef"
            v-bind="{ ...$attrs, ...fieldProps }"
            @focus="focus()"
            @blur="blur()"
          >
            <template v-if="$slots['context-menu']" #context-menu="slotData"><slot name="context-menu" v-bind="slotData" /></template>
          </markdown-field-content>
        </template>
      </s-field>
    </template>
  </s-input>
</template>

<script setup lang="ts">
const markdownRef = useTemplateRef('markdownRef');
function onControlClick() {
  markdownRef.value?.focus();
}
</script>

<style lang="scss" scoped>
.v-field__input {
  padding: 0 1px !important;
  cursor: initial !important;
  row-gap: 0;
}
</style>
