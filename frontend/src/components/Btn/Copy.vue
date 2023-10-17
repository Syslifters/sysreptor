<template>
  <btn-confirm
    button-text="Duplicate"
    button-icon="mdi-clipboard-multiple-outline"
    dialog-title="Confirm Duplication"
    :button-variant="props.buttonVariant"
    :tooltip-text="props.tooltipText"
    :dialog-text="props.confirmText"
    :action="performCopy"
  />
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  copy: () => Promise<void>;
  tooltipText?: string;
  confirmText?: string;
  buttonVariant?: string;
}>(), {
  tooltipText: 'Duplicate',
  confirmText: undefined,
  buttonVariant: 'list-item',
});

async function performCopy() {
  await props.copy();
  successToast('Duplicated successfully');
}
</script>
