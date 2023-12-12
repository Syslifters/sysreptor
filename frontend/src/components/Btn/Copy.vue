<template>
  <btn-confirm
    button-text="Duplicate"
    button-icon="mdi-clipboard-multiple-outline"
    dialog-title="Confirm Duplication"
    :button-variant="props.buttonVariant"
    :dialog-text="props.confirmText"
    :action="performCopy"
  />
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  copy: () => Promise<void>;
  confirmText?: string;
  buttonVariant?: string;
}>(), {
  confirmText: undefined,
  buttonVariant: 'list-item',
});

async function performCopy() {
  await props.copy();
  successToast('Duplicated successfully');
}
</script>
