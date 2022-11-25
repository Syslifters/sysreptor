<template>
  <v-card
    flat tile
    class="drag-drop-area"
    @drop.prevent="performImport($event.dataTransfer.files)" 
    @dragover.prevent="showDropArea = true" 
    @dragenter.prevent="showDropArea = true" 
    @dragleave.prevent="showDropArea = false"
  >
    <s-btn @click="$refs.fileInput.click()" :loading="importInProgress" color="primary" v-bind="$attrs">
      <v-icon>mdi-upload</v-icon>
      Import
    </s-btn>
    <input ref="fileInput" type="file" @change="performImport($event.target.files)" class="d-none" :disabled="disabled || importInProgress" />

    <v-fade-transition v-if="!disabled">
      <v-overlay v-if="showDropArea" absolute>
        <div class="text-center">
          Import file
        </div>
      </v-overlay>
    </v-fade-transition>
  </v-card>
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
      showDropArea: false,
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
        this.showDropArea = false;

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

<style lang="scss" scoped>
.drag-drop-area {
  display: inline-block;
  border-width: 0;
}
</style>
