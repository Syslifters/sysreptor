<template>
  <div 
    ref="imgContainerRef"
    class="img-container zoom-on-hover" 
    :class="{ 'zoomed': isZoomed }"
    @mouseenter="zoomHover = true"
    @mouseleave="zoomHover = false"
    @mousemove="moveZoom"
    @click="zoomEnabled = !zoomEnabled"
  >
    <img ref="imgNormalRef" :src="props.src" class="img-normal" />
    <img ref="imgZoomRef" :src="props.src" class="img-zoom" :style="{ 'transform': `scale(${props.scaleFactor})` }" />
  </div>
</template>

<script setup lang="ts">
const zoomEnabled = defineModel<boolean>();
const props = withDefaults(defineProps<{
  src: string;
  scaleFactor?: number;
}>(), {
  scaleFactor: 3,
});

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
