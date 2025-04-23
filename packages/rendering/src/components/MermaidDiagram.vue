<template>
  <template v-if="!diagramPng">
    <pre ref="codeContainerRef" v-bind="$attrs">
      <slot name="default" />
    </pre>
    <img ref="svgContainerRef" :src="diagramSvg || undefined" alt="" v-bind="$attrs" />
    <canvas ref="canvasRef" />
  </template>
  <div v-else class="mermaid-diagram" v-bind="$attrs">
    <img :src="diagramPng" alt="" />
  </div>
</template>

<script lang="ts">
import { getCurrentInstance, onMounted, ref } from 'vue';
import { mermaid } from '@sysreptor/markdown';
import { useRenderTask } from '@/utils';

mermaid.initialize({
  startOnLoad: false,
  theme: 'neutral',
  securityLevel: 'strict',
});
</script>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  text?: string|null;
}>(), {
  text: null,
});

const diagramSvg = ref<string|null>(null);
const diagramPng = ref<string|null>(null);

const codeContainerRef = ref<HTMLElement>();
const svgContainerRef = ref<HTMLImageElement>();
const canvasRef = ref<HTMLCanvasElement>();

const vm = getCurrentInstance();

function unescapeCode(code: string) {
  return code.replaceAll('&#x7B;', '{').replaceAll('&#x7D;', '}');
}

onMounted(useRenderTask(async () => { 
  // Ensure custom fonts are loaded
  await document.fonts.ready;

  // Get meramid code from slot
  const codeContainer = codeContainerRef.value!;
  const mermaidCode = props.text || unescapeCode(codeContainer.innerText);

  // Render mermaid code to SVG
  let svg = null;
  try {
    const res = await mermaid.render(`mermaid-${vm!.uid}`, mermaidCode, codeContainer);
    svg = res.svg;
  } catch (e: any) {
    console.warn('mermaid error', { message: 'Mermaid error', details: e.message });
    // Show mermaid error image in PDF
    svg = codeContainer.querySelector('svg')!.outerHTML;
  }

  // Convert SVG to PNG, because weasyprint does not support all required SVG features.
  // Diagrams would not be displayed correctly.
  const svgImg = svgContainerRef.value!;
  const canvas = canvasRef.value!;
  try {
    // First, render SVG to <img> tag
    const waitSvgLoaded = new Promise<void>((resolve, reject) => {
      svgImg.addEventListener('load', () => resolve(), { once: true });
      svgImg.addEventListener('error', () => reject(new Error('Failed to render mermaid diagram from SVG to PNG')), { once: false });
    });
    diagramSvg.value = `data:image/svg+xml;charset=utf-8;base64,${btoa(unescape(encodeURIComponent(svg)))}`;
    await waitSvgLoaded;

    // Then, render SVG from <img> to canvas
    // Only works with <img> tags and not <svg> directly, therefore we need the previous step
    canvas.width = svgImg.width;
    canvas.height = svgImg.height;
    canvas.getContext('2d')?.drawImage(svgImg, 0, 0, canvas.width, canvas.height);
  } catch (e: any) {
    console.error('mermaid error', { message: 'Mermaid error', details: e.message });
    // Continue with an empty image
  }

  // Finally, export canvas contents as PNG
  diagramPng.value = canvas.toDataURL('image/png');
}))
</script>
