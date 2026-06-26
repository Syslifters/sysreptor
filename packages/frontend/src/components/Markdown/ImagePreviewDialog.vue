<template>
  <s-dialog 
    v-if="modelValue" 
    ref="dialogRef"
    :model-value="true" 
    @update:model-value="onClose"
    :persistent="editMode"
    width="90vw"
    max-width="90%"
    height="90vh"
    max-height="90%"
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
        v-if="!editMode && originalImageSrc"
        :action="openOriginalDialog"
        :confirm="false"
        :disabled="fetchOriginalImageInfo.pending.value"
        button-variant="icon"
        button-text="View original"
        tooltip-text="View Original Image"
        class="dialog-toolbar-btn"
      >
        <template #icon>
          <v-badge icon="mdi-undo-variant" location="bottom right" color="surface" offset-y="4">
            <v-icon size="large" icon="mdi-image-outline" />
          </v-badge>
        </template>
      </btn-confirm>
      <btn-confirm
        v-if="editMode && originalImageSrc"
        :action="revertToOriginal"
        :confirm="true"
        :disabled="props.readonly"
        button-variant="icon"
        button-icon="mdi-undo-variant"
        button-text="Revert"
        tooltip-text="Revert to Original Image"
        class="dialog-toolbar-btn"
      >
        <template #icon>
          <v-icon size="large" icon="mdi-undo-variant" />
        </template>
        <template #dialog-text>
          <p class="mt-0">
            Are you sure you want to revert to the original image? This will discard all annotations and edits you've made to this image.
          </p>
          <v-img :src="originalImageSrc" />
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
        class="dialog-toolbar-btn"
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
        :tooltip-text="hasUnsavedChanges ? 'Save Changes' : 'Everything saved'"
        class="dialog-toolbar-btn"
      >
        <template #icon>
          <v-badge dot :color="hasUnsavedChanges ? 'error' : 'success'">
            <v-icon size="x-large" icon="mdi-content-save" />
          </v-badge>
        </template>
      </btn-confirm>
    </template>

    <v-divider />
    <v-card-text ref="dialogBodyRef" class="pa-0 flex-grow-height" tabindex="-1">
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

  <s-dialog
    v-if="modelValue"
    v-model="originalDialogOpen"
    width="80vw"
    max-width="80%"
    height="80vh"
    max-height="80%"
    density="compact"
  >
    <template #title>
      <span>Original Image</span>
    </template>
    <template #toolbar>
      <btn-confirm
        :action="revertToOriginalAndClose"
        :confirm="true"
        :disabled="props.readonly || !originalImageSrc"
        button-variant="icon"
        button-text="Revert"
        tooltip-text="Revert to Original Image"
        class="dialog-toolbar-btn"
      >
        <template #icon>
          <v-icon size="large" icon="mdi-undo-variant" />
        </template>
        <template #dialog-text>
          <p class="mt-0">
            Are you sure you want to revert to the original image? This will discard all annotations and edits you've made to this image.
          </p>
        </template>
      </btn-confirm>
    </template>
    <v-divider />
    <v-card-text class="pa-0 flex-grow-height">
      <div v-if="fetchOriginalImageInfo.pending.value" class="pa-4 d-flex justify-center">
        <v-progress-circular indeterminate />
      </div>
      <markdown-image-preview-zoom
        v-if="originalImageSrc"
        :src="originalImageSrc"
      />
    </v-card-text>
  </s-dialog>
</template>

<script setup lang="ts">
import { useAbortController } from '@base/utils/helpers';

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
const wasOpenedInEditMode = ref(false);
const currentImageInfo = ref<UploadedFileInfo|null>(null);
const originalImageInfo = ref<UploadedFileInfo|null>(null);
const saveInProgress = ref(false);
const originalDialogOpen = ref(false);

const hasUnsavedChanges = computed((): boolean => !!imageEditorRef.value?.hasChanges);

watch(modelValue, async () => {
  editMode.value = false;
  wasOpenedInEditMode.value = false;
  saveInProgress.value = false;
  originalDialogOpen.value = false;
  currentImageInfo.value = null;
  originalImageInfo.value = null;
  // Reset zoom when navigating to another image
  await nextTick();
  imageZoomRefs.value?.forEach(ref => ref?.resetZoom?.());

  await resolveOriginalInfo();
});

function exitEditMode() {
  if (wasOpenedInEditMode.value) {
    // Close dialog
    modelValue.value = null;
  }
  wasOpenedInEditMode.value = false;
  editMode.value = false;
}

function onClose(val: boolean) {
  if (!val) {
    if (editMode.value) {
      if (imageEditorRef.value?.hasChanges) {
        const confirmClose = window.confirm('Do you really want to leave? You have unsaved changes!');
        if (!confirmClose) {
          return;
        }
      }
      exitEditMode();
    } else {
      modelValue.value = null;
    }
  }
}

const originalImageSrc = computed(() => {
  if (!originalImageInfo.value?.name || !currentImageInfo.value?.name || !modelValue.value?.src) {
    return null;
  }
  return modelValue.value.src.replace('/' + currentImageInfo.value.name, '/' + originalImageInfo.value.name);
});

watch(editMode, async () => {
  if (editMode.value) {
    await resolveOriginalInfo();
  }
});
async function getImageInfoById(id: string, signal: AbortSignal) {
  const imageApiUrl = new URL(modelValue.value!.src).pathname.replace(/\/name\/.*/, '/' + id);
  return await $fetch<UploadedFileInfo>(imageApiUrl, { method: 'GET', signal });
}

async function getImageInfoFromSrc(imageSrc: string|null|undefined, signal: AbortSignal) {
  if (!imageSrc) {
    return null;
  }

  try {
    const res = await $fetch.raw(imageSrc, { method: 'HEAD', signal });
    const fileId = res.headers.get('X-Sysreptor-Id');
    if (!fileId) {
      return null;
    }

    return await getImageInfoById(fileId, signal);
  } catch {
    return null;
  }
}

const fetchOriginalImageInfo = useAbortController(async ({ signal }) => {
  const src = modelValue.value?.src;
  if (!src) {
    return;
  }

  const img = await getImageInfoFromSrc(src, signal);
  if (signal.aborted) {
    return;
  }

  currentImageInfo.value = img;

  if (!img?.original) {
    originalImageInfo.value = null;
    return;
  }

  const original = await getImageInfoById(img.original, signal);
  if (signal.aborted) {
    return;
  }
  originalImageInfo.value = original;
});

async function resolveOriginalInfo() {
  if (!modelValue.value?.src) {
    fetchOriginalImageInfo.abort();
    return;
  }

  try {
    await fetchOriginalImageInfo.run();
  } catch {
    return;
  }
}

async function openOriginalDialog() {
  await resolveOriginalInfo();
  if (!originalImageSrc.value) {
    return;
  }
  originalDialogOpen.value = true;
}

async function revertToOriginalAndClose() {
  await revertToOriginal();
  originalDialogOpen.value = false;
}


function updateImageUrlInMarkdown(newMd: string) {
  if (!modelValue.value) {
    return;
  }

  // Extract URLs from markdown and emit event to update editor
  const imageUrlRegex = /(\]\(|src=")(?<url>\s*\/[^\s)?"]+)/;
  const oldUrl = modelValue.value?.markdown?.match(imageUrlRegex)?.groups?.url;
  const newUrl = newMd.match(imageUrlRegex)?.groups?.url;
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

  if (!hasUnsavedChanges.value) {
    exitEditMode();
    return;
  }

  // Export annotated image
  const blob = await imageEditorRef.value?.exportAsBlob();
  if (!blob) {
    throw new Error('Failed to export image');
  }
  const file = new File([blob], 'edited.png', { type: 'image/png' });
  const newMd = await props.uploadFile(file, { 
    original: originalImageInfo.value?.id || currentImageInfo.value?.id || null,
  });

  updateImageUrlInMarkdown(newMd);
  // Close dialog and show success
  exitEditMode();
  successToast('Image saved successfully');
}

async function revertToOriginal() {
  if (!originalImageInfo.value || !currentImageInfo.value || !modelValue.value?.markdown || props.readonly) {
    return;
  }

  const newMd = modelValue.value.markdown.replaceAll('/' + currentImageInfo.value.name, '/' + originalImageInfo.value.name);
  updateImageUrlInMarkdown(newMd);

  // Update model and exit edit mode
  exitEditMode();
  successToast('Reverted to original image');
}

async function open(image: PreviewImage, editModeParam?: boolean) {
  modelValue.value = image;
  await nextTick();
  editMode.value = !!editModeParam;
  wasOpenedInEditMode.value = editMode.value;
}


function preventMdeUndoRedo(e: InputEvent|KeyboardEvent) {
  if (!modelValue.value) {
    return;
  }
  if (
    (e instanceof InputEvent && ['historyUndo', 'historyRedo'].includes(e.inputType)) ||
    (e instanceof KeyboardEvent && (e.metaKey || e.ctrlKey) && ['z', 'y'].includes(e.key.toLowerCase()))
  ) {
    // Prevent background undo/redo from affecting the markdown editor
    e.preventDefault();
    e.stopImmediatePropagation();
  }
}
useEventListener(window, 'beforeinput', preventMdeUndoRedo);
useEventListener(window, 'keydown', preventMdeUndoRedo);


defineExpose({
  open,
});
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

.dialog-toolbar-btn {
  color: inherit;
}
</style>
