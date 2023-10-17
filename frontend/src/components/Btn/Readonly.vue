<template>
  <btn-confirm
    v-if="props.value"
    :action="() => performAction(false)"
    :confirm="true"
    button-text="Re-activate"
    button-icon="mdi-reload"
    tooltip-text="Mark as active and allow editing"
    dialog-text="Mark this project as active and allow editing."
  />
  <btn-confirm
    v-else
    :action="() => performAction(true)"
    :confirm="true"
    button-text="Finish"
    button-icon="mdi-flag-checkered"
    tooltip-text="Mark as finished and make it readonly"
    dialog-text="Mark this project as finished and make it readonly. You and other users will not be able to edit this project, sections and findings."
  />
</template>

<script setup lang="ts">
const props = defineProps<{
  value: boolean;
  setReadonly: (val: boolean) => Promise<void>;
}>();

async function performAction(val: boolean) {
  await props.setReadonly(val);
  if (val) {
    successToast('Finished project');
  } else {
    successToast('Re-activated project');
  }
}
</script>
