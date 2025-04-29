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
      >
        <template #default="{ props: fieldProps }">
          <markdown-diff-field-content
            ref="markdownRef"
            v-bind="{...props, ...$attrs, ...fieldProps }"
          />
        </template>
      </s-field>
    </template>
  </s-input>
</template>

<script setup lang="ts">
const props = defineProps<{
  historic: DiffFieldProps,
  current: DiffFieldProps,
}>();
</script>

<style lang="scss" scoped>
.v-field__input {
  padding: 0 1px !important;
  cursor: initial !important;
  row-gap: 0;
}
</style>
