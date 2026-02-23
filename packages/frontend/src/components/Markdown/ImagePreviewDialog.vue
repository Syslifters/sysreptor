<template>
  <s-dialog 
    v-if="modelValue" 
    :model-value="true" 
    @update:model-value="onClose"
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
      <template v-if="!editMode">
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
        
        <s-btn-icon
          v-if="props.uploadFile"
          @click="openImageEditor"
          density="compact"
        >
          <v-icon size="small" icon="mdi-image-edit-outline" />
          <s-tooltip activator="parent" location="top" text="Edit Image" />
        </s-btn-icon>
      </template>
      
      <template v-else>
        <span>Edit Image</span>
        <s-btn-secondary
          @click="editMode = false"
          prepend-icon="mdi-close"
          class="mr-2"
        >
          Cancel
        </s-btn-secondary>
        <s-btn-primary
          prepend-icon="mdi-content-save"
          :loading="saving"
        >
          Save
        </s-btn-primary>
      </template>
    </template>
    
    <v-card-text class="pa-0 flex-grow-height">
      <v-window
        v-if="!editMode"
        ref="windowRef"
        v-model="modelValue"
        show-arrows="hover"
        :continuous="true"
      >
        <v-window-item v-for="image in props.images" :key="image.src" :value="image">
          <template v-if="!editMode || image.src !== modelValue?.src">
            <markdown-image-preview-zoom
              v-model="zoomEnabled"
              :src="image.src"
            />
          </template>
          
          <template v-else>
            <image-editor
              ref="imageEditorRef"
              :image-src="image.src"
            />
          </template>
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
import { VWindow } from 'vuetify/components';
import ImageEditor from '~/components/Markdown/ImageEditor.vue';

const modelValue = defineModel<PreviewImage|null>();
const props = defineProps<{
  images: PreviewImage[];
  scaleFactor?: number;
  uploadFile?: (file: File) => Promise<string>;
  rewriteFileUrlMap?: Record<string, string>;
}>();

const windowRef = useTemplateRef('windowRef');

function onClose(val: boolean) {
  if (!val) {
    modelValue.value = null;
  }
}

const zoomEnabled = ref(false);
watch(modelValue, () => {
  zoomEnabled.value = false;
});

// Image Editor
const editMode = ref(false);
const saving = ref(false);

function openImageEditor() {
  if (modelValue.value) {
    editMode.value = true;
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
