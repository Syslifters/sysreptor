<template>
  <btn-confirm
    button-text="Delete"
    button-icon="mdi-delete"
    button-color="error"
    dialog-title="Confirm Delete?"
    dialog-text="Do you really want to delete this item? This action is not reversible!"
    :color="buttonVariant !== 'icon' ? 'error' : ($attrs.color || 'default')"
    :button-variant="buttonVariant"
    :confirm="confirm"
    :confirm-input="confirmInput"
    :action="props.delete"
  />
</template>

<script setup lang="ts">
import type { BtnConfirmVariant } from "@/components/Btn/Confirm.vue";

const props = withDefaults(defineProps<{
  delete: (() => Promise<void>)|(() => void),
  buttonVariant?: BtnConfirmVariant,
  confirm?: boolean,
  confirmInput?: string,
}>(), {
  buttonVariant: 'default',
  icon: false,
  confirm: true,
  confirmInput: undefined,
});
</script>
