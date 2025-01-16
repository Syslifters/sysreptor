<template>
  <v-menu
    v-model="colorPickerVisible"
    :disabled="props.disabled"
    :close-on-content-click="false"
    min-width="0"
  >
    <template #activator="activatorSlotProps">
      <slot name="activator" v-bind="activatorSlotProps" />
    </template>
    <template #default>
      <v-color-picker
        v-model="modelValue"
        :disabled="props.disabled"
        mode="hex"
        :modes="['hex']"
      />
    </template>
  </v-menu>
</template>

<script setup lang="ts">
const modelValue = defineModel<string|null>();
const props = defineProps<{
  disabled?: boolean;
}>();

const colorPickerVisible = ref(false);

</script>
