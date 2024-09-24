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
    @keydown.arrow-left="windowRef?.group.prev()"
    @keydown.arrow-right="windowRef?.group.next()"
  >
    <template #title>
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
    <v-card-text class="pa-0 flex-grow-height">
      <v-window
        ref="windowRef"
        v-model="modelValue"
        show-arrows="hover"
        :continuous="true"
      >
        <v-window-item v-for="image in props.images" :key="image.src" :value="image">
          <markdown-image-preview-zoom
            v-model="zoomEnabled"
            :src="image.src"
          />
        </v-window-item>
      </v-window>
    </v-card-text>
  </s-dialog>
</template>

<script setup lang="ts">
import { VWindow } from 'vuetify/components';

const modelValue = defineModel<PreviewImage|null>();
const props = defineProps<{
  images: PreviewImage[];
  scaleFactor?: number;
}>();

const windowRef = ref<VWindow>()

function onClose(val: boolean) {
  if (!val) {
    modelValue.value = null;
  }
}

const zoomEnabled = ref(false);
watch(modelValue, () => {
  zoomEnabled.value = false;
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
</style>
