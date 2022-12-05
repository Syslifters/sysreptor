<template>
  <btn-confirm 
    :button-text="buttonText"
    :button-icon="buttonIcon"
    :tooltip-text="tooltipText"
    dialog-title="Confirm Duplication"
    :dialog-text="confirmText"
    :action="performCopy"
    v-bind="$attrs"
  />
</template>

<script>
export default {
  props: {
    copy: {
      type: Function,
      required: true,
    },
    buttonText: {
      type: String,
      default: 'Duplicate',
    },
    buttonIcon: {
      type: String,
      default: 'mdi-clipboard-multiple-outline',
    },
    tooltipText: {
      type: String,
      default: 'Duplicate',
    },
    confirmText: {
      type: String,
      default: null,
    }
  },
  methods: {
    async performCopy() {
      await this.copy();
      this.$toast.success('Duplicated successfuly');
    }
  }
}
</script>
