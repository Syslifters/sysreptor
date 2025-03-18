<template>
  <btn-confirm
    button-text="Delete"
    button-icon="mdi-delete"
    button-color="error"
    dialog-title="Confirm Delete?"
    dialog-text="Do you really want to delete this item? This action is not reversible!"
    :color="props.buttonVariant !== 'icon' ? 'error' : (props.color || 'default')"
    :button-variant="props.buttonVariant"
    :confirm="props.confirm"
    :confirm-input="props.confirmInput"
    :action="props.delete"
  />
</template>

<script setup lang="ts">
import type { BtnConfirmVariant } from "@base/components/Btn/Confirm.vue";

const props = withDefaults(defineProps<{
  delete: (() => Promise<void>)|(() => void),
  buttonVariant?: BtnConfirmVariant,
  confirm?: boolean,
  confirmInput?: string,
  color?: string;
}>(), {
  buttonVariant: 'default',
  icon: false,
  confirm: true,
  confirmInput: undefined,
  color: undefined,
});
</script>
