<template>
  <btn-confirm
    button-text="Duplicate"
    button-icon="mdi-content-copy"
    dialog-title="Confirm Duplication"
    :button-variant="props.buttonVariant"
    :dialog-text="props.confirmText"
    :action="performCopy"
  />
</template>

<script setup lang="ts">
import type { BtnConfirmVariant } from './Confirm.vue';

const props = withDefaults(defineProps<{
  copy: () => Promise<void>|void;
  confirmText?: string;
  buttonVariant?: BtnConfirmVariant;
}>(), {
  confirmText: undefined,
  buttonVariant: 'list-item',
});

async function performCopy() {
  await Promise.resolve(props.copy());
  successToast('Duplicated successfully');
}
</script>
