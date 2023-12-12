<template>
  <template v-if="!diagramPng">
    <pre ref="refCodeContainer" v-bind="$attrs">
      <slot name="default" />
    </pre>
    <img ref="refSvgContainer" :src="diagramSvg" alt="" v-bind="$attrs" />
    <canvas ref="refCanvas" />
  </template>
  <div v-else class="mermaid-diagram" v-bind="$attrs">
    <img :src="diagramPng" alt="" />
  </div>
</template>

<script>
import { mermaid } from 'reportcreator-markdown';

mermaid.initialize({
  startOnLoad: false,
  theme: 'neutral',
  securityLevel: 'strict',
});

export default {
  props: {
    text: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      diagramSvg: null,
      diagramPng: null,
    }
  },
  async mounted() {
    // Ensure custom fonts are loaded
    await document.fonts.ready;

    // Get meramid code from slot
    const codeContainer = this.$refs.refCodeContainer;
    const mermaidCode = this.text || codeContainer.innerText;

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
    const svgImg = this.$refs.refSvgContainer;
    const canvas = this.$refs.refCanvas;
    try {
      // First, render SVG to <img> tag
      const waitSvgLoaded = new Promise((resolve, reject) => {
        svgImg.addEventListener('load', () => resolve(), { once: true });
        svgImg.addEventListener('error', () => reject(new Error('Failed to render mermaid diagram from SVG to PNG')), { once: false });
      });
      this.diagramSvg = `data:image/svg+xml;charset=utf-8;base64,${btoa(unescape(encodeURIComponent(svg)))}`;
      await waitSvgLoaded;

      // Then, render SVG from <img> to canvas
      // Only works with <img> tags and not <svg> directly, therefore we need the previous step
      canvas.width = svgImg.width;
      canvas.height = svgImg.height;
      canvas.getContext('2d').drawImage(svgImg, 0, 0, canvas.width, canvas.height);
    } catch (e) {
      console.error('mermaid error', { message: 'Mermaid error', details: e.message });
      // Continue with an empty image
    }
    
    // Finally, export canvas contents as PNG
    this.diagramPng = canvas.toDataURL('image/png');
  },
}
</script>
