<template>
  <canvas v-if="!chartImageData" ref="canvasRef" 
    :width="chartWidth || (width * 50)" 
    :height="chartHeight || (height * 50)" 
  />
  <img v-else :src="chartImageData" alt="" :style="{width: width + 'cm', height: height + 'cm'}"   />
</template>

<script setup lang="ts">
import { useRenderTask } from '@/utils';
import Chart from 'chart.js/auto';
import { ref, nextTick, onMounted, useTemplateRef } from 'vue';

const props = withDefaults(defineProps<{
  config: any;
  // Width and height in cm
  width?: number;
  height?: number;
  // Optional pixel width and height of chart canvas
  chartWidth?: number|null;
  chartHeight?: number|null;
}>(), {
  width: 15,
  height: 10,
  chartWidth: null,
  chartHeight: null,
});

const canvasRef = ref<HTMLCanvasElement>();  // useTemplateRef results in runtime warnings
const chartImageData = ref<string|null>(null);

onMounted(useRenderTask(async () => {
  // Ensure custom fonts are loaded
  await document.fonts.ready;

  // Wait for canvas to be ready
  while (!canvasRef.value) {
    chartImageData.value = null;
    await nextTick();
  }

  // Render chart
  const chart = new Chart(canvasRef.value, {
    ...props.config,
    options: {
      ...(props.config.options || {}),
      responsive: false,
      animation: false,
    }
  });
  chartImageData.value = chart.toBase64Image();
  chart.destroy();
}));
</script>
