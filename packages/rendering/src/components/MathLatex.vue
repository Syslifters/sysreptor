<template>
  <pre v-if="!renderedHtml" ref="codeContainerRef" v-bind="$attrs">
    <slot name="default" />
  </pre>
  <component 
    v-else
    :is="katexOptions.displayMode ? 'div' : 'span'"  
    class="math-latex language-math"
    :class="katexOptions.displayMode ? 'math-display' : 'math-inline'"
    v-bind="$attrs" 
    v-html="renderedHtml" 
  />
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRenderTask } from '@/utils';
import { katex } from '@sysreptor/markdown';
import 'katex/dist/katex.min.css';

const props = withDefaults(defineProps<{
  text?: string | null;
  displayMode?: boolean | string;
}>(), {
  text: null,
  displayMode: true,
});

const katexOptions = computed<Partial<katex.KatexOptions>>(() => ({
  displayMode: String(props.displayMode).toLowerCase() === 'true',
  output: 'html',
}));

const codeContainerRef = ref<HTMLElement>();
const renderedHtml = ref<string>('');

function unescapeCode(code: string) {
  return code.replaceAll('&#x7B;', '{').replaceAll('&#x7D;', '}');
}

onMounted(useRenderTask(async () => { 
  // Get expression from prop or slot content
  const codeContainer = codeContainerRef.value!;
  const expression = props.text || unescapeCode(codeContainer.innerText);

  try {
    renderedHtml.value = katex.renderToString(expression, {
      ...katexOptions.value,
      throwOnError: true,
    });
  } catch (e: any) {
    console.warn('LaTeX math error', { message: 'LaTeX math error', details: e.message });

    if (e instanceof katex.ParseError) {
      // Try rendering again with throwOnError false to show partial output
      renderedHtml.value = katex.renderToString(expression, {
        ...katexOptions.value,
        throwOnError: false,
      });
    }
  }
}));
</script>

