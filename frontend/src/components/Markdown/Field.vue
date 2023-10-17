<template>
  <s-input class="v-text-field" v-bind="$attrs">
    <template #default="{id, isDirty, isDisabled, isReadonly }">
      <s-field
        v-bind="$attrs"
        :id="id.value"
        :dirty="isDirty.value"
        :active="true"
        :disabled="isDisabled.value"
        :readonly="isReadonly.value"
        @click="onControlClick"
      >
        <template #default="{ props: fieldProps, focus, blur }">
          <markdown-field-content
            ref="markdownRef"
            v-bind="{ ...$attrs, ...fieldProps }"
            @focus="focus()"
            @blur="blur()"
          />
        </template>
      </s-field>
    </template>
  </s-input>
</template>

<script setup lang="ts">
const markdownRef = ref();
function onControlClick() {
  markdownRef.value?.focus();
}
</script>

<style lang="scss" scoped>
.v-field__input {
  padding: 0 1px !important;
  cursor: initial !important;
}
</style>
