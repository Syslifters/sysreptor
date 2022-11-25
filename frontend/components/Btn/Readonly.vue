<template>
  <btn-confirm
    v-if="value"
    :action="() => setReadonly(false)"
    button-text="Re-activate"
    button-icon="mdi-reload"
    tooltip-text="Mark as active and allow editing"
    dialog-text="Mark this project as active and allow editing."
    v-bind="$attrs"
  />
  <btn-confirm 
    v-else
    :action="() => setReadonly(true)"
    button-text="Finish"
    button-icon="mdi-flag-checkered"
    tooltip-text="Mark as finished and make it readonly"
    dialog-text="Mark this project as finished and make it readonly. You and other users will not be able to edit this project, sections and findings."
    v-bind="$attrs"
  />
</template>

<script>
export default {
  props: {
    value: {
      type: Boolean,
      required: true,
    },
    setReadonly: {
      type: Function,
      required: true,
    },
  },
}
</script>
