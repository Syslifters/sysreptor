<template>
  <div>
    <!-- Rendered markdown gets sanitized in renderMarkdownToHtml -->
    <!-- eslint-disable-next-line vue/no-v-html -->
    <div ref="previewRef" v-html="renderedMarkdown" @click.stop class="preview" />
    <markdown-image-preview-dialog v-model="previewImageSrc" :images="previewImagesAll" />
  </div>
</template>

<script lang="ts">
import { mermaid } from '@sysreptor/markdown';
import { uuidv4 } from "@base/utils/helpers";
import { renderMarkdownToHtmlInWorker, type ReferenceItem } from '~/composables/markdown';
import 'highlight.js/styles/default.css';

mermaid.initialize({
  startOnLoad: false,
  theme: 'neutral',
  securityLevel: 'strict',
});
</script>

<script setup lang="ts">
const props = defineProps<{
  value?: string|null;
  rewriteFileUrlMap?: Record<string, string>;
  referenceItems?: ReferenceItem[];
  cacheBuster?: string;
}>();

const cacheBusterFallback = uuidv4();
const cacheBuster = computed(() => props.cacheBuster || cacheBusterFallback);
const renderedMarkdown = ref('');
const renderedMarkdownText = ref('');
watchThrottled(() => props.value, async () => {
  const mdText = props.value || '';
  renderedMarkdown.value = await renderMarkdownToHtmlInWorker({
    text: mdText,
    preview: true,
    referenceItems: toRaw(props.referenceItems),
    rewriteFileUrlMap: props.rewriteFileUrlMap,
    cacheBuster: cacheBuster.value,
  });
  renderedMarkdownText.value = mdText;

  await nextTick();
  postProcessRenderedHtml();
}, { throttle: 500, leading: true, immediate: true });

const previewRef = useTemplateRef('previewRef');
async function postProcessRenderedHtml() {
  if (!previewRef.value) {
    return;
  }

  // Prevent navigation when clicking on anchor links in preview
  previewRef.value.querySelectorAll('.preview a[href^="#"]').forEach((a: Element) => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.querySelector(a.getAttribute('href')!);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  // Render mermaid diagrams
  const mermaidNodes = previewRef.value.querySelectorAll<HTMLElement>('.preview div.mermaid-diagram');
  try {
    await mermaid.run({ nodes: mermaidNodes });
  } catch (e: any) {
    // eslint-disable-next-line no-console
    console.error('Mermaid error: ' + e.message, e);
  }
}
whenever(previewRef, postProcessRenderedHtml, { immediate: true });

const previewImageSrc = ref<PreviewImage|null>(null);
const previewImagesAll = ref<PreviewImage[]>([]);
function showPreviewImage(event: MouseEvent) {
  const imgElement = event.target as HTMLImageElement;
  if (previewRef.value && imgElement && imgElement.tagName === 'IMG' && imgElement.src) {
    // Collect all images in the preview
    previewImagesAll.value = Array.from(previewRef.value.querySelectorAll('img')).map((img: HTMLImageElement) => {
      const captionEl = img.parentElement?.querySelector('figcaption');

      let markdown = undefined;
      try {
        const position = JSON.parse(img.parentElement?.getAttribute('data-position') || '');
        if (Number.isInteger(position?.start?.offset) && Number.isInteger(position?.end?.offset)) {
          markdown = renderedMarkdownText.value.substring(position.start.offset, position.end.offset) || undefined;
        }
      } catch {
        // Ignore error
      }
      return {
        src: img.src,
        caption: captionEl?.innerText,
        markdown,
      };
    });
    // Select the clicked image
    previewImageSrc.value = previewImagesAll.value.find(img => img.src === imgElement.src) || null;

    event.stopPropagation();
  }
}
useEventListener(previewRef, 'click', showPreviewImage);

defineExpose({
  element: previewRef,
})

</script>

<style lang="scss" scoped>
@use "sass:meta";
@use "@base/assets/vuetify.scss" as vuetify;

.preview {
  overflow: auto;
  word-wrap: break-word;
  margin: 4px 0.5em;
}

.preview > :deep(*:first-child) {
  margin-top: 0;
}

.preview :deep() {
  @include meta.load-css("@/assets/rendering/base-text.css");

  .footnotes {
    border-top: 1px solid currentColor;
    margin-top: 2em;
    padding-top: 0.3em;

    h4 {
      font-size: 1em;
      margin-top: 0;
    }
  }

  code {
    background-color: vuetify.$code-background-color;
    color: vuetify.$code-color;
  }
  blockquote {
    background-color: rgba(var(--v-theme-on-surface), 0.05);
    border-left: 5px solid rgba(var(--v-theme-on-surface), 0.3);
  }
  table, th, td {
    border-color: rgb(var(--v-border-color));
  }

  figure img {
    cursor: zoom-in;
  }

  .file-download-preview {
    display: inline-flex;
    text-align: center;
    font-size: inherit;
    text-decoration: none;

    &::before {
      font-size: 20pt;
    }
  }

  .ref {
    color: inherit;
    font-style: inherit;
    text-decoration: underline;
  }

  .mermaid-diagram svg {
    width: 100%;
    max-width: 100% !important;
  }
}
</style>
