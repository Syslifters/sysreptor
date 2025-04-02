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
import { defineProps, ref, nextTick, onMounted } from 'vue';

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

const canvasRef = ref();
const chartImageData = ref<string|null>(null);

const renderChartImage = useRenderTask(async () => {
  // Ensure custom fonts are loaded
  await document.fonts.ready;

  // Render chart
  if (chartImageData.value) {
    chartImageData.value = null;
    await nextTick();
  }
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
});
onMounted(renderChartImage);
</script>
