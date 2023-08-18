<template>
  <div
    class="drag-drop-area"
    @drop.prevent="onDrop" 
    @dragover.prevent="showDropArea = true" 
    @dragenter.prevent="showDropArea = true" 
    @dragleave.prevent="showDropArea = false"
  >
    <slot name="default" />

    <v-fade-transition v-if="!disabled">
      <v-overlay v-if="showDropArea" absolute>
        <div class="text-center mt-10">
          <h2>Drop files to upload</h2>
        </div>
      </v-overlay>
    </v-fade-transition>
  </div>
</template>

<script>
export default {
  props: {
    disabled: {
      type: Boolean,
      default: false,
    },
    multiple: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['drop'],
  data() {
    return {
      showDropArea: false,
    };
  },
  methods: {
    onDrop(event) {
      this.showDropArea = false;
      
      if (this.disabled) {
        return;
      }

      const files = Array.from(event.dataTransfer.files);
      if (!this.multiple && files.length > 1) {
        this.$toast.error('Only one file can be uploaded at a time');
        return;
      }
      this.$emit('drop', files);
    },
  },
}
</script>

<style lang="scss" scoped>
.drag-drop-area {
  min-height: 100%;
}
</style>
