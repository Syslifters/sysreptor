<template>
  <s-btn-icon
    @click="fileInput.click()"
    :loading="props.loading || importInProgress"
    :disabled="props.disabled"
    color="secondary"
    variant="flat"
  >
    <v-icon icon="mdi-upload" />
    <input
      ref="fileInput"
      type="file"
      accept=".tar.gz"
      @change="performImport(($event.target as HTMLInputElement)?.files)"
      class="d-none"
      :disabled="disabled || props.loading || importInProgress"
    />

    <s-tooltip activator="parent" location="bottom" text="Import from file" />
  </s-btn-icon>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  import: (file: File) => Promise<void>;
  loading?: boolean;
  disabled?: boolean;
}>(), {
  loading: false,
  disabled: false
});

const importInProgress = ref(false);
const fileInput = ref();

async function performImport(files?: FileList|null) {
  const file = Array.from(files || [])[0];
  if (props.disabled || importInProgress.value || !file) {
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
