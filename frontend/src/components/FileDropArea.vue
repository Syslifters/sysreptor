<template>
  <div
    class="drag-drop-area"
    @drop.prevent="onDrop"
    @dragover.prevent="showDropArea = true"
    @dragenter.prevent="showDropArea = true"
    @dragleave.prevent="showDropArea = false"
  >
    <slot name="default" />

    <v-overlay
      :model-value="showDropArea"
      :disabled="disabled || !showDropArea"
      contained
      content-class="w-100 h-100"
    >
      <div class="h-100 d-flex justify-center align-center text-white">
        <h2>Drop files to upload</h2>
      </div>
    </v-overlay>
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  disabled?: boolean,
  multiple?: boolean,
}>(), {
  disabled: false,
  multiple: false,
});
const emit = defineEmits<{
  (e: 'drop', files: File[]): void,
}>();

const showDropArea = ref(false);
function onDrop(event: DragEvent) {
  showDropArea.value = false;
  if (props.disabled) {
    return;
  }

  const files = Array.from(event.dataTransfer?.files || []);
  if (!props.multiple && files.length > 1) {
    errorToast('Only one file can be uploaded at a time');
    return;
  }
  emit('drop', files);
}
</script>

<style lang="scss" scoped>
.drag-drop-area {
  position: relative;
  min-height: 100%;
}
</style>
