<template>
  <s-btn @click="$refs.fileInput.click()" :loading="importInProgress" color="primary" v-bind="$attrs">
    <v-icon>mdi-upload</v-icon>
    Import

    <input ref="fileInput" type="file" @change="performImport($event.target.files)" class="d-none" :disabled="disabled || importInProgress" />
  </s-btn>
</template>

<script>
export default {
  props: {
    import: {
      type: Function,
      required: true,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      importInProgress: false,
    }
  },
  methods: {
    async performImport(files) {
      const file = Array.from(files)[0];
      if (this.importInProgress) {
        return;
      }
      
      try {
        this.importInProgress = true;

        await this.import(file);
      } catch (error) {
        let message = 'Import failed';
        if (error?.response?.status === 400 && error?.response?.data?.format) {
          message += ': ' + error.response.data.format[0];
        }
        this.$toast.global.requestError({ error, message });
      } finally {
        this.importInProgress = false;
        this.$refs.fileInput.value = null;
      }
    }
  }
}
</script>
