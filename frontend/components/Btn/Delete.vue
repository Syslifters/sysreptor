<template>
  <btn-confirm
    button-text="Delete"
    button-icon="mdi-delete"
    button-color="error"
    dialog-title="Confirm Delete?"
    dialog-text="Do you really want to delete this item? This action is not reversible!"
    :color="!icon ? 'error' : ($attrs.color || 'default')"
    :icon="icon"
    :confirm="confirm"
    :confirm-input="confirmInput"
    :action="$props.delete"
    v-bind="$attrs"
  />
</template>

<script>
export default {
  props: {
    icon: {
      type: Boolean,
      default: false,
    },
    confirm: {
      type: Boolean,
      default: true,
    },
    confirmInput: {
      type: String,
      default: null,
    },
    delete: {
      type: Function,
      required: true,
    }
  },
}
</script>
