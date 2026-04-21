<template>
  <s-dialog 
    v-if="modelValue" 
    ref="dialogRef"
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
        v-if="editMode && editedImageInfo?.original && originalImageSrc"
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
        tooltip-text="Save Changes"
        class="dialog-toolbar-btn"
      >
        <template #icon>
          <v-icon size="x-large" icon="mdi-content-save" />
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

const dialogRef = useTemplateRef('dialogRef');
const windowRef = useTemplateRef('windowRef');
const imageEditorRef = useTemplateRef('imageEditorRef');
const imageZoomRefs = ref<any[]>([]);

// function isUndoRedoKeydown(e: KeyboardEvent) {
//   const key = e.key.toLowerCase();
//   const mod = e.metaKey || e.ctrlKey;
//   if (!mod) { return false; }
//   return key === 'z' || key === 'y';
// }

// function isHistoryBeforeInput(e: Event): e is InputEvent {
//   return (e as InputEvent)?.inputType === 'historyUndo' || (e as InputEvent)?.inputType === 'historyRedo';
// }

// /**
//  * When this dialog is open, the underlying CodeMirror editor can still receive native undo/redo
//  * via `beforeinput` (inputType=historyUndo/historyRedo) if focus is not properly trapped.
//  * We prevent these events at capture phase so they never reach CodeMirror.
//  */
// function preventBackgroundUndoRedo() {
//   const onKeydownCapture = (e: KeyboardEvent) => {
//     if (!modelValue.value) { return; }
//     if (!isUndoRedoKeydown(e)) { return; }
//     // If the dialog didn't get focus for some reason, prevent undo/redo from affecting background editors.
//     e.preventDefault();
//     e.stopImmediatePropagation();
//   };
//   const onBeforeInputCapture = (e: Event) => {
//     if (!modelValue.value) { return; }
//     if (!isHistoryBeforeInput(e)) { return; }
//     // This is the event CodeMirror's history() listens to. Prevent it while dialog is open.
//     e.preventDefault();
//     e.stopImmediatePropagation();
//   };

//   // Capture on window so we see the event before any component/editor handlers.
//   window.addEventListener('keydown', onKeydownCapture);
//   window.addEventListener('beforeinput', onBeforeInputCapture);
//   return () => {
//     window.removeEventListener('keydown', onKeydownCapture);
//     window.removeEventListener('beforeinput', onBeforeInputCapture);
//   };
// }

// const cleanupPreventUndoRedo = shallowRef<null | (() => void)>(null);
// watch(modelValue, (val) => {
//   cleanupPreventUndoRedo.value?.();
//   cleanupPreventUndoRedo.value = null;
//   if (val) {
//     cleanupPreventUndoRedo.value = preventBackgroundUndoRedo();
//   }
// }, { immediate: true });
// onBeforeUnmount(() => cleanupPreventUndoRedo.value?.());

const editMode = ref(false);
const wasOpenedInEditMode = ref(false);
const editedImageInfo = ref<Omit<UploadedFileInfo, 'original'> & { original: UploadedFileInfo|null }|null>(null);
const saveInProgress = ref(false);
watch(modelValue, async () => {
  editMode.value = false;
  wasOpenedInEditMode.value = false;
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
      if (wasOpenedInEditMode.value) {
        // Close dialog
        modelValue.value = null;
      }
    } else {
      modelValue.value = null;
    }
  }
}

const originalImageSrc = computed(() => {
  if (!editedImageInfo.value?.original?.name || !modelValue.value?.src) {
    return null;
  }
  return modelValue.value.src.replace('/' + editedImageInfo.value.name, '/' + editedImageInfo.value.original.name);
});

watch(editMode, async () => {
  if (editMode.value) {
    const img = await getImageInfoFromSrc(modelValue.value?.src || '');
    editedImageInfo.value = img ? {
      ...img,
      original: img?.original ? await getImageInfoById(img.original) : null,
    } : null;
  } else {
    editedImageInfo.value = null;
  }
});
async function getImageInfoById(id: string) {
  const imageApiUrl = new URL(modelValue.value!.src).pathname.replace(/\/name\/.*/, '/' + id);
  return await $fetch<UploadedFileInfo>(imageApiUrl, { method: 'GET' });
}
async function getImageInfoFromSrc(imageSrc?: string|null) {
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
  const file = new File([blob], 'edited.png', { type: 'image/png' });
  const newMd = await props.uploadFile(file, { 
    original: editedImageInfo.value?.original?.id || editedImageInfo.value?.id || null,
  });

  updateImageUrlInMarkdown(newMd);
  // Close dialog and show success
  successToast('Image saved successfully');
  editMode.value = false;
  wasOpenedInEditMode.value = false;
}

async function revertToOriginal() {
  if (!editedImageInfo.value?.original || !modelValue.value?.markdown || props.readonly) {
    return;
  }

  const newMd = modelValue.value.markdown.replaceAll('/' + editedImageInfo.value.name, '/' + editedImageInfo.value.original.name);
  updateImageUrlInMarkdown(newMd);

  // Update model and exit edit mode
  successToast('Reverted to original image');
  editMode.value = false;
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
