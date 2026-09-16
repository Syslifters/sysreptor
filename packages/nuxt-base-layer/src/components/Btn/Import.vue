<template>
  <s-btn-icon
    v-if="buttonVariant === 'icon'"
    @click="fileInput?.click()"
    :loading="props.loading || importInProgress"
    :disabled="props.disabled"
    color="secondary"
    variant="flat"
    density="comfortable"
  >
    <v-icon icon="mdi-upload" />
    <input
      ref="fileInput"
      type="file"
      data-testid="import-input"
      accept=".tar.gz,application/gzip"
      multiple
      @change="performImport(($event.target as HTMLInputElement)?.files)"
      class="d-none"
      :disabled="disabled || props.loading || importInProgress"
    />

    <v-tooltip activator="parent" location="bottom" text="Import from file" />
  </s-btn-icon>
  <v-list-item
    v-else
    link
    @click="fileInput?.click()"
    :disabled="props.disabled"
  >
    <template #prepend>
      <v-progress-circular v-if="props.loading || importInProgress" indeterminate size="24" />
      <v-icon v-else icon="mdi-upload" />
    </template>
    <template #default>
      <v-list-item-title>Import</v-list-item-title>
      <input
        ref="fileInput"
        type="file"
        accept=".tar.gz,application/gzip"
        multiple
        @change="performImport(($event.target as HTMLInputElement)?.files)"
        class="d-none"
        :disabled="disabled || props.loading || importInProgress"
      />
    </template>
  </v-list-item>    
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  import: (files: File[]) => Promise<void>;
  loading?: boolean;
  disabled?: boolean;
  buttonVariant?: 'icon' | 'list-item';
}>(), {
  loading: false,
  disabled: false,
  buttonVariant: 'icon',
});

const importInProgress = ref(false);
const fileInput = useTemplateRef('fileInput');

async function performImport(files?: FileList|File[]|null) {
  const fileList = Array.from(files || []);
  if (props.disabled || importInProgress.value || fileList.length === 0) {
    return;
  }

  try {
    importInProgress.value = true;

    await props.import(fileList);
  } catch (error: any) {
    let message = 'Import failed';
    if (error?.status === 400 && error?.data?.format) {
      message += ': ' + (Array.isArray(error.data.format) ? error.data.format[0] : error.data.format);
    }
    requestErrorToast({ error, message });
  } finally {
    importInProgress.value = false;
    if (fileInput.value) {
      fileInput.value.value = '';
    }
  }
}

defineExpose({
  performImport
});
</script>
