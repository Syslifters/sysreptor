<template>
  <s-btn
    @click="fileInput.click()"
    :loading="importInProgress"
    color="primary"
    prepend-icon="mdi-upload"
  >
    Import
    <input
      ref="fileInput"
      type="file"
      @change="performImport($event.target.files)"
      class="d-none"
      :disabled="disabled || importInProgress"
    />
  </s-btn>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  import: (file: File) => Promise<void>;
  disabled?: boolean;
}>(), {
  disabled: false
});

const importInProgress = ref(false);
const fileInput = ref();

async function performImport(files: FileList) {
  const file = Array.from(files)[0];
  if (props.disabled || importInProgress.value) {
    return;
  }

  try {
    importInProgress.value = true;

    await props.import(file);
  } catch (error: any) {
    let message = 'Import failed';
    if (error?.status === 400 && error?.data?.format) {
      message += ': ' + error.data.format[0];
    }
    requestErrorToast({ error, message });
  } finally {
    importInProgress.value = false;
    if (fileInput.value) {
      fileInput.value.value = null;
    }
  }
}

defineExpose({
  performImport
});
</script>
