<template>
  <canvas v-if="!this.chartImageData" ref="canvas" 
    :width="chartWidth || (width * 50)" 
    :height="chartHeight || (height * 50)" 
  />
  <img v-else :src="this.chartImageData" alt="" :style="{width: width + 'cm', height: height + 'cm'}"   />
</template>

<script>
import Chart from 'chart.js/auto';

export default {
  name: "Chart",
  props: {
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
  },
  data() {
    return {
      chartImageData: null,
    };
  },
  mounted() {
    const chart = new Chart(this.$refs.canvas, {
      ...this.config,
      options: {
        ...(this.config.options || {}),
        responsive: false,
        animation: false,
      }
    });
    this.chartImageData = chart.toBase64Image();
    chart.destroy();
  },
}
</script>
