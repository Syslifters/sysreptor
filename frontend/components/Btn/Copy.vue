<template>
  <btn-confirm 
    button-text="Duplicate"
    button-icon="mdi-clipboard-multiple-outline"
    :tooltip-text="tooltipText"
    dialog-title="Confirm Duplication"
    :dialog-text="confirmText"
    :action="performCopy"
  />
</template>

<script>
export default {
  props: {
    copy: {
      type: Function,
      required: true,
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
  data() {
    return {
      copyInProgress: false,
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
