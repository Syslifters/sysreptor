<template>
  <s-dialog 
    v-if="props.modelValue" 
    :model-value="true" 
    @update:model-value="onClose"
    max-width="90vw"
    max-height="90vh"
    class="img-dialog"
  >
    <template #title>{{ props.modelValue.caption || '' }}</template>
    <div 
      ref="imgContainerRef"
      class="img-container zoom-on-hover" 
      :class="{ 'zoomed': isZoomed }"
      @mouseenter="zoomHover = true"
      @mouseleave="zoomHover = false"
      @mousemove="moveZoom"
      @click="zoomEnabled = !zoomEnabled"
    >
      <img ref="imgNormalRef" :src="props.modelValue.src" class="img-normal" />
      <img ref="imgZoomRef" :src="props.modelValue.src" class="img-zoom" :style="{ 'transform': `scale(${props.scaleFactor})` }" />
    </div>
  </s-dialog>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  modelValue?: PreviewImage|null;
  scaleFactor?: number;
}>(), {
  modelValue: null,
  scaleFactor: 3,
});
const emit = defineEmits<{
  'update:modelValue': [value: PreviewImage|null];
}>();

function onClose(val: boolean) {
  if (!val) {
    emit('update:modelValue', null);
    zoomEnabled.value = false;
  }
}

const zoomEnabled = ref(false);
const zoomHover = ref(false);
const isZoomed = computed(() => zoomEnabled.value && zoomHover.value);

const imgContainerRef = ref<HTMLElement>();
const imgNormalRef = ref<HTMLElement>();
const imgZoomRef = ref<HTMLElement>();

function pageOffset(el: HTMLElement) {
  // get the left and top offset of a dom block element
  const rect = el.getBoundingClientRect();
  const scrollLeft = document.documentElement.scrollLeft;
  const scrollTop = document.documentElement.scrollTop;
  return {
    y: rect.top + scrollTop,
    x: rect.left + scrollLeft
  }
}

function moveZoom(event: MouseEvent) {
  if (!zoomHover.value) { return; }
  const offset = pageOffset(imgContainerRef.value!);
  const relativeX = event.clientX - offset.x + window.scrollX
  const relativeY = event.clientY - offset.y + window.scrollY
  const normalFactorX = relativeX / imgNormalRef.value!.offsetWidth
  const normalFactorY = relativeY / imgNormalRef.value!.offsetHeight
  const x = normalFactorX * (imgZoomRef.value!.offsetWidth * props.scaleFactor - imgNormalRef.value!.offsetWidth)
  const y = normalFactorY * (imgZoomRef.value!.offsetHeight * props.scaleFactor - imgNormalRef.value!.offsetHeight)
  imgZoomRef.value!.style.left = -x + "px"
  imgZoomRef.value!.style.top = -y + "px"
}

onUpdated(() => {
  if (imgContainerRef.value) {
    // Set explicit height to fit image height into dialog.
    // Otherwise, img does not respect height of parent element.
    imgContainerRef.value.style.height = `${imgContainerRef.value.clientHeight}px`;
  }
})

</script>

<style lang="scss" scoped>
.img-container {
  width: 100%;
  height: 100%;

  img {
    display: block;
    width: 100%;
    height: 100%;
    object-fit: contain;
    padding: 1rem;
  }
}

.zoom-on-hover {
  position: relative;
  overflow: hidden;
  cursor: zoom-in;

  .img-zoom {
    position: absolute;
    opacity: 0;
    transform-origin: top left;
  }
}
.zoom-on-hover.zoomed {
  cursor: zoom-out;
  .img-zoom {
    opacity: 1;
  }
  .img-normal {
    opacity: 0;
  }
}
</style>
