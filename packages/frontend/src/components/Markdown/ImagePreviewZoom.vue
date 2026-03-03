<template>
  <div 
    ref="containerEl"
    class="image-preview-container"
  >
    <div 
      class="image-wrapper elevation-4"
      :class="{ 'cursor-zoom-in': zoomFactor <= 1, 'cursor-zoom-out': zoomFactor > 1 }"
      :style="{ 
        width: scaledSize.width + 'px', 
        height: scaledSize.height + 'px' 
      }"
      @click="toggleZoom"
    >
      <img 
        ref="imgEl" 
        :src="props.src" 
        @load="onImageLoad"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useZoomImage } from '@base/utils/helpers';

const props = defineProps<{
  src: string;
}>();

const containerEl = useTemplateRef('containerEl');
const imgEl = useTemplateRef('imgEl');
const intrinsicSize = ref<{ width: number; height: number } | null>(null);
const { scaledSize, zoomFactor, setZoom, resetZoom } = useZoomImage(containerEl, intrinsicSize);

function onImageLoad() {
  if (imgEl.value) {
    intrinsicSize.value = {
      width: imgEl.value.naturalWidth,
      height: imgEl.value.naturalHeight,
    };
  }
}

function toggleZoom(event: MouseEvent) {
  if (zoomFactor.value <= 1) {
    setZoom(3, event);
  } else {
    setZoom(1, event);
  }
}

defineExpose({ resetZoom });
</script>

<style lang="scss" scoped>
.image-preview-container {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  overflow: auto;
  padding: 0.5rem;
  touch-action: none;
}

.image-wrapper {
  background: 
    repeating-conic-gradient(rgb(var(--v-theme-surface)) 0% 25%, rgba(var(--v-theme-on-surface), 0.1) 0% 50%) 
    50% / 20px 20px;

  & > img {
    display: block;
    width: 100%;
    height: 100%;
    user-select: none;
  }
}

.cursor-zoom-in {
  cursor: zoom-in;
}

.cursor-zoom-out {
  cursor: zoom-out;
}
</style>
