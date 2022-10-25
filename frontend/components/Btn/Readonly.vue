<template>
  <btn-confirm
    v-if="value"
    :action="() => setReadonly(false)"
    button-text="Set as active"
    tooltip-text="Mark as active and allow editing"
    dialog-text="Mark this project as active and allow editing."
  />
  <btn-confirm 
    v-else
    :action="() => setReadonly(true)"
    button-text="Set as finished"
    tooltip-text="Mark as finished and make it readonly"
    dialog-text="Mark this project as finished and make it readonly. You and other users will not be able to edit this project, sections and findings."
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
