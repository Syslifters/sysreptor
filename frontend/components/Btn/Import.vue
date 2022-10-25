<template>
  <s-btn @click="$refs.fileInput.click()" :loading="importInProgress" color="primary" v-bind="$attrs">
    <v-icon>mdi-upload</v-icon>
    Import
    <input ref="fileInput" type="file" @change="performImport" class="d-none" />
  </s-btn>
</template>

<script>
export default {
  props: {
    import: {
      type: Function,
      required: true,
    }
  },
  data() {
    return {
      importInProgress: false,
    }
  },
  methods: {
    async performImport(event) {
      const file = Array.from(event.target.files)[0];
      if (this.importInProgress) {
        return;
      }
      this.importInProgress = true;
      try {
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
