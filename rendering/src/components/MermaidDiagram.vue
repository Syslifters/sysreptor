<template>
  <template v-if="!diagramPng">
    <pre ref="refCodeContainer" v-bind="$attrs">
      <slot name="default" />
    </pre>
    <img v-if="diagramSvg" ref="refSvgContainer" :src="diagramSvg" alt="" v-bind="$attrs" />
    <canvas ref="refCanvas" />
  </template>
  <div v-else class="mermaid-diagram" v-bind="$attrs">
    <img :src="diagramPng" alt="" />
  </div>
</template>

<script>
import { mermaid } from 'reportcreator-markdown';
import { nextTick } from 'vue';

mermaid.initialize({
  startOnLoad: false,
  theme: 'neutral',
  securityLevel: 'strict',
});

export default {
  data() {
    return {
      diagramSvg: null,
      diagramPng: null,
    }
  },
  async mounted() {
    // Get meramid code from slot
    const codeContainer = this.$refs.refCodeContainer;
    const mermaidCode = codeContainer.innerText;

    // Render mermaid code to SVG
    let svg = null;
    try {
      const res = await mermaid.render(`mermaid-${this.$.uid}`, mermaidCode, codeContainer);
      svg = res.svg;
    } catch (e) {
      console.warn('mermaid error', { message: 'Mermaid error', details: e.message });
      // Show mermaid error image in PDF
      svg = codeContainer.querySelector('svg').outerHTML;
    }

    // Convert SVG to PNG, because weasyprint does not support all required SVG features.
    // Diagrams would not be displayed correctly.
    // First, render SVG to <img> tag
    this.diagramSvg = `data:image/svg+xml;charset=utf-8;base64,${btoa(unescape(encodeURIComponent(svg)))}`;
    await nextTick();
    const svgImg = this.$refs.refSvgContainer;

    // Then, render SVG from <img> to canvas
    // Only works with <img> tags and not <svg> directly, therefore we need the previous step
    const canvas = this.$refs.refCanvas;
    canvas.width = svgImg.width;
    canvas.height = svgImg.height;
    canvas.getContext('2d').drawImage(svgImg, 0, 0, canvas.width, canvas.height);
    
    // Finally, export canvas contents as PNG
    this.diagramPng = canvas.toDataURL('image/png');
  },
}
</script>
