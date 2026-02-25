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
      <s-btn-icon
        v-if="props.uploadFile && !editMode"
        @click="editMode = true"
        :disabled="props.readonly || !modelValue.markdown"
      >
        <v-icon size="large" icon="mdi-image-edit-outline" />
        <s-tooltip activator="parent" text="Edit Image" />
      </s-btn-icon>
      <s-btn-icon
        v-if="editMode"
        @click="performSave"
        :disabled="props.readonly || saveInProgress"
        :loading="saveInProgress"
      >
        <v-icon size="x-large" icon="mdi-check-bold" />
        <s-tooltip activator="parent" text="Save" />
      </s-btn-icon>
    </template>

    <v-divider />
    <v-card-text class="pa-0 flex-grow-height">
      <v-window
        v-if="!editMode"
        ref="windowRef"
        v-model="modelValue"
        show-arrows="hover"
        :continuous="true"
      >
        <v-window-item v-for="image in props.images" :key="image.src" :value="image">
          <markdown-image-preview-zoom
            ref="imageZoomRefs"
            v-model="zoomEnabled"
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
const zoomEnabled = ref(false);
const saveInProgress = ref(false);
watch(modelValue, async () => {
  editMode.value = false;
  zoomEnabled.value = false;
  saveInProgress.value = false;
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

async function getOriginalImageInfo(imageSrc: string) {
  try {
    const res = await $fetch.raw(imageSrc, { method: 'HEAD' });
    return res.headers.get('X-Sysreptor-Id');
  } catch {
    return null;
  }
}

async function performSave() {
  if (!props.uploadFile || !modelValue.value || props.readonly) {
    return;
  }

  if (!imageEditorRef.value?.hasChanges) {
    editMode.value = false;
    return;
  }

  try {
    saveInProgress.value = true;

    // Export annotated image
    const blob = await imageEditorRef.value?.exportAsBlob();
    if (!blob) {
      throw new Error('Failed to export image');
    }
    const original = await getOriginalImageInfo(modelValue.value.src);
    const file = new File([blob], 'edited.png', { type: 'image/png' });
    const newMd = await props.uploadFile(file, { 
      original: original 
    });

    // Extract URLs from markdown and emit event to update editor
    const oldUrl = modelValue.value.markdown?.match(/\]\(\/[^\s)?"]+/)?.[0]?.substring(2);
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

    // Close dialog and show success
    successToast('Image saved successfully');
    modelValue.value.src = modelValue.value.src.replace(oldUrl, newUrl);
    modelValue.value.markdown = newMarkdown;
    editMode.value = false;
  } catch (error) {
    errorToast((error as Error).message || 'Failed to save image');
  } finally {
    saveInProgress.value = false;
  }
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
