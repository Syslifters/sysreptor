<template>
  <s-dialog v-model="dialogVisible" :disabled="disabled">
    <template #activator="{on, attrs}">
      <s-btn
        @click="showDialog"
        v-bind="attrs"
        v-on="on"
        icon
        small
      >
        <v-icon small>mdi-pencil</v-icon>
      </s-btn>
    </template>
    <template #title>Edit</template>
    <template #default>
      <v-card-text>
        <design-layout-component-form 
          v-model="form" 
          :lang="item.context.projectType.language"
          :upload-file="uploadFile"
          :rewrite-file-url="rewriteFileUrl"
          :disabled="disabled" 
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <s-btn @click="dialogVisible = false" color="secondary">Cancel</s-btn>
        <s-btn @click="saveDialog" color="primary">Save</s-btn>
      </v-card-actions>
    </template>
  </s-dialog>
</template>

<script>
export default {
  props: {
    item: {
      type: Object,
      required: true,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    uploadFile: {
      type: Function,
      default: null,
    },
    rewriteFileUrl: {
      type: Function,
      default: null,
    },
  },
  data() {
    return {
      dialogVisible: false,
      form: null,
    };
  },
  methods: {
    showDialog() {
      if (!this.form) {
        this.form = this.item.component.getUpdateForm(this.item);
      }
      this.dialogVisible = true;
    },
    saveDialog() {
      this.dialogVisible = false;
      this.$emit('update', this.item.component.update(this.item, this.form));
    }
  }
}
</script>
