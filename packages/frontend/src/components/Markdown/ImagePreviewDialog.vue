<template>
  <s-dialog 
    v-if="modelValue" 
    :model-value="true" 
    @update:model-value="onClose"
    :persistent="editMode"
    width="90vw"
    max-width="90vw"
    height="90vh"
    max-height="90vh"
    density="compact"
    :card-props="{ class: 'img-preview-dialog-card' }"
    @keydown.arrow-left="!editMode && windowRef?.group.prev()"
    @keydown.arrow-right="!editMode && windowRef?.group.next()"
  >
    <template #title>
      <span v-if="editMode" class="mr-2">Edit Image</span>

      <v-code v-if="modelValue.markdown" class="d-inline">
        <s-btn-icon
          @click="copyToClipboard(modelValue.markdown)"
          icon="mdi-content-copy"
          size="small"
          density="compact"
        />
          {{ modelValue.markdown }}
      </v-code>
      <span v-else>{{ modelValue.caption || '' }}</span>
    </template>

    <template #toolbar>
      <btn-confirm
        v-if="editMode && editedImageInfo?.original"
        :action="revertToOriginal"
        :confirm="true"
        :disabled="props.readonly"
        button-variant="icon"
        button-icon="mdi-undo-variant"
        button-text="Revert"
        tooltip-text="Revert to Original Image"
        dialog-text="Are you sure you want to revert to the original image? This will discard all annotations and edits you've made to this image."
      >
        <template #icon>
          <v-icon size="large" icon="mdi-undo-variant" />
        </template>
      </btn-confirm>
      <btn-confirm
        v-if="props.uploadFile && !editMode"
        :action="() => { editMode = true; }"
        :confirm="false"
        :disabled="props.readonly || saveInProgress"
        button-variant="icon"
        button-text="Edit Image"
        tooltip-text="Edit Image"
      >
        <template #icon>
          <v-icon size="large" icon="mdi-image-edit-outline" />
        </template>
      </btn-confirm>
      <btn-confirm
        v-if="editMode"
        :action="performSave"
        :confirm="false"
        :disabled="props.readonly || saveInProgress"
        button-variant="icon"
        button-text="Save"
        tooltip-text="Save Changes"
      >
        <template #icon>
          <v-icon size="x-large" icon="mdi-check-bold" />
        </template>
      </btn-confirm>
    </template>

    <v-divider />
    <v-card-text class="pa-0 flex-grow-height">
      <v-window
        v-if="!editMode"
        ref="windowRef"
        v-model="modelValue"
        :show-arrows="props.images.length > 1 ? 'hover' : false"
        :continuous="true"
      >
        <v-window-item v-for="image in props.images" :key="image.src" :value="image">
          <markdown-image-preview-zoom
            ref="imageZoomRefs"
            :src="image.src"
          />
        </v-window-item>
      </v-window>
      <markdown-image-editor
        v-else
        ref="imageEditorRef"
        :image-src="modelValue.src"
      />
    </v-card-text>
  </s-dialog>
</template>

<script setup lang="ts">
const modelValue = defineModel<PreviewImage|null>();
const props = defineProps<{
  images: PreviewImage[];
  readonly?: boolean;
  scaleFactor?: number;
  uploadFile?: (file: File, body?: Record<string, any>) => Promise<string>;
  rewriteFileUrlMap?: Record<string, string>;
}>();
const emit = defineEmits<{
  'image-edited': [value: { oldUrl: string; newUrl: string; oldMarkdown: string|null; newMarkdown: string|null; }];
}>();

const windowRef = useTemplateRef('windowRef');
const imageEditorRef = useTemplateRef('imageEditorRef');
const imageZoomRefs = ref<any[]>([]);

const editMode = ref(false);
const editedImageInfo = ref<UploadedFileInfo|null>(null);
const saveInProgress = ref(false);
watch(modelValue, async () => {
  editMode.value = false;
  saveInProgress.value = false;
  editedImageInfo.value = null;
  // Reset zoom when navigating to another image
  await nextTick();
  imageZoomRefs.value?.forEach(ref => ref?.resetZoom?.());
});

function onClose(val: boolean) {
  if (!val) {
    if (editMode.value) {
      if (imageEditorRef.value?.hasChanges) {
        const confirmClose = window.confirm('Do you really want to leave? You have unsaved changes!');
        if (!confirmClose) {
          return;
        }
      }
      editMode.value = false;
    } else {
      modelValue.value = null;
    }
  }
}

watch(editMode, async () => {
  if (editMode.value) {
    editedImageInfo.value = await getOriginalImageInfo(modelValue.value?.src || '');
  } else {
    editedImageInfo.value = null;
  }
});
async function getImageInfoById(id: string) {
  const imageApiUrl = new URL(modelValue.value!.src).pathname.replace(/\/name\/.*/, '/' + id);
  return await $fetch<UploadedFileInfo>(imageApiUrl, { method: 'GET' });
}
async function getOriginalImageInfo(imageSrc?: string|null) {
  if (!imageSrc) {
    return null;
  }

  try {
    const res = await $fetch.raw(imageSrc, { method: 'HEAD' });
    const fileId = res.headers.get('X-Sysreptor-Id');
    if (!fileId) {
      return null;
    }

    return await getImageInfoById(fileId);
  } catch {
    return null;
  }
}


function updateImageUrlInMarkdown(newMd: string) {
  if (!modelValue.value) {
    return;
  }

  // Extract URLs from markdown and emit event to update editor
  const oldUrl = modelValue.value?.markdown?.match(/\]\(\/[^\s)?"]+/)?.[0]?.substring(2);
  const newUrl = newMd.match(/\]\(\/[^\s)?"]+/)?.[0]?.substring(2);
  if (!oldUrl || !newUrl) {
    throw new Error('Failed to save image: Could not extract URLs');
  }
  const newMarkdown = modelValue.value.markdown ? modelValue.value.markdown.replaceAll(oldUrl, newUrl) : null;
  emit('image-edited', {
    oldUrl,
    newUrl,
    oldMarkdown: modelValue.value.markdown || null,
    newMarkdown,
  });

  modelValue.value.src = modelValue.value.src.replace(oldUrl, newUrl);
  modelValue.value.markdown = newMarkdown;
}
async function performSave() {
  if (!props.uploadFile || !modelValue.value || props.readonly) {
    return;
  }

  if (!imageEditorRef.value?.hasChanges) {
    editMode.value = false;
    return;
  }

  // Export annotated image
  const blob = await imageEditorRef.value?.exportAsBlob();
  if (!blob) {
    throw new Error('Failed to export image');
  }
  const original = editedImageInfo.value || await getOriginalImageInfo(modelValue.value.src);
  const file = new File([blob], 'edited.png', { type: 'image/png' });
  const newMd = await props.uploadFile(file, { 
    original: original?.original || original?.id || null,
  });

  updateImageUrlInMarkdown(newMd);
  // Close dialog and show success
  successToast('Image saved successfully');
  editMode.value = false;
}

async function revertToOriginal() {
  if (!editedImageInfo.value?.original || !modelValue.value?.markdown || props.readonly) {
    return;
  }

  const originalInfo = await getImageInfoById(editedImageInfo.value.original);
  const newMd = modelValue.value.markdown.replaceAll('/' + editedImageInfo.value.name, '/' + originalInfo.name);
  updateImageUrlInMarkdown(newMd);

  // Update model and exit edit mode
  successToast('Reverted to original image');
  editMode.value = false;
}
</script>

<style lang="scss">
.img-preview-dialog-card {
  height: 100%;
  width: 100%;

  .v-window, .v-window__container, .v-window-item {
    height: 100%;
  }

  :deep(.v-toolbar__content > .v-spacer) {
    // display: none;
    min-width: 0
  }
}
</style>
