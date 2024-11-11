<template>
  <canvas v-if="!chartImageData" ref="canvasRef" 
    :width="chartWidth || (width * 50)" 
    :height="chartHeight || (height * 50)" 
  />
  <img v-else :src="chartImageData" alt="" :style="{width: width + 'cm', height: height + 'cm'}"   />
</template>

<script setup>
import Chart from 'chart.js/auto';
import { defineProps, ref, nextTick, onMounted } from 'vue';

const props = defineProps({
  config: {
    type: Object,
    required: true,
  },
  // Width and height in cm
  width: {
    type: Number,
    default: 15,
  },
  height: {
    type: Number,
    default: 10,
  },
  // Optional pixel width and height of chart canvas
  chartWidth: {
    type: Number,
    default: null,
  },
  chartHeight: {
    type: Number,
    default: null,
  }
});

const canvasRef = ref();
const chartImageData = ref(null);

async function renderChartImage() {
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
}
onMounted(async () => {
  // Ensure custom fonts are loaded
  await document.fonts.ready;
  // Render chart
  await renderChartImage();
});
</script>
