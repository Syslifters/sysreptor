<template>
  <div
    class="drag-drop-area"
    @drop.prevent="onDrop"
    @dragover="onDragEnter"
    @dragenter="onDragEnter"
    @dragleave="onDragLeave"
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
import debounce from 'lodash/debounce';

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
const hideDropArea = debounce(() => {
  showDropArea.value = false;
}, 100);

function onDragEnter(event: DragEvent) {
  if ((event.dataTransfer?.types || []).includes('Files')) {
    event.preventDefault();
    showDropArea.value = true;
    hideDropArea.cancel();
  }
}
function onDragLeave() {
  hideDropArea();
}

function onDrop(event: DragEvent) {
  hideDropArea();
  if (props.disabled || !(event.dataTransfer?.types || []).includes('Files')) {
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
