<template>
  <v-dialog v-model="confirmDialogVisible" max-width="500">
    <template #activator="{on: dialogOn, attrs: dialogAttrs}">
      <s-tooltip>
        <template #activator="{on: tooltipOn, attrs: tooltipAttrs}">
          <s-btn
            color="secondary"
            v-bind="{...$props, ...dialogAttrs, ...tooltipAttrs}" 
            v-on="{...dialogOn, ...tooltipOn}"
          >
            <v-icon>mdi-clipboard-multiple-outline</v-icon>
            Duplicate
          </s-btn>
        </template>

        <template #default>
          <slot name="tooltip">
            <span>Duplicate</span>
          </slot>
        </template>
      </s-tooltip>
    </template>

    <s-card>
      <v-card-title>Confirm Duplication</v-card-title>
      <v-card-text><slot name="confirm-text"></slot></v-card-text>
      <v-divider />
      <v-card-actions>
        <v-spacer />
        <s-btn @click="confirmDialogVisible = false">Cancel</s-btn>
        <s-btn color="primary" @click="performCopy">
          <v-icon>mdi-clipboard-multiple-outline</v-icon>
          Duplicate
        </s-btn>
      </v-card-actions>
    </s-card>
  </v-dialog>
</template>

<script>
export default {
  emits: ['copy'],
  data() {
    return {
      confirmDialogVisible: false,
    }
  },
  methods: {
    performCopy() {
      this.confirmDialogVisible = false;
      this.$emit('copy');
    }
  }
}
</script>
