<template>
  <div>
    <!-- eslint-disable-next-line vue/no-v-html -->
    <div ref="previewRef" v-html="renderedMarkdown" @click.stop class="preview" />
    <markdown-image-preview-dialog v-model="previewImageSrc" />
  </div>
</template>

<script lang="ts">
import { v4 as uuidv4 } from 'uuid';
import throttle from 'lodash/throttle';
// @ts-ignore
import { renderMarkdownToHtml, mermaid } from 'reportcreator-markdown';
import { absoluteApiUrl } from '~/utils/urls';

mermaid.initialize({
  startOnLoad: false,
  theme: 'neutral',
  securityLevel: 'strict',
});
</script>

<script setup lang="ts">
const props = defineProps<{
  value?: string|null;
  rewriteFileUrl?: (fileSrc: string) => string;
  rewriteReferenceLink?: (src: string) => {href: string, title: string}|null;
  cacheBuster?: string;
}>();

const renderedMarkdown = ref('');
const cacheBusterFallback = uuidv4();
const cacheBuster = computed(() => props.cacheBuster || cacheBusterFallback);

function rewriteFileSource(imgSrc: string) {
  // Rewrite image source to handle image fetching from markdown.
  // Images in markdown are referenced with a URL relative to the parent resource (e.g. "/images/name/image.png").
  if (!props.rewriteFileUrl || !imgSrc.startsWith('/')) {
    return imgSrc;
  }

  return absoluteApiUrl(props.rewriteFileUrl(`${imgSrc}?c=${cacheBuster.value}`));
}
const updatePreviewThrottled = throttle(() => {
  // Render markdown to HTML
  renderedMarkdown.value = renderMarkdownToHtml(props.value || '', {
    preview: true,
    rewriteFileSource,
    rewriteReferenceLink: props.rewriteReferenceLink,
  });
});
watch(() => props.value, () => updatePreviewThrottled(), { immediate: true });

const previewRef = ref<HTMLDivElement>();
async function postProcessRenderedHtml() {
  // Prevent navigation when clicking on anchor links in preview
  previewRef.value!.querySelectorAll('.preview a[href^="#"]').forEach((a: Element) => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.querySelector(a.getAttribute('href')!);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  // Render mermaid diagrams
  const mermaidNodes = previewRef.value!.querySelectorAll<HTMLElement>('.preview div.mermaid-diagram');
  try {
    await mermaid.run({ nodes: mermaidNodes });
  } catch (e: any) {
    // eslint-disable-next-line no-console
    console.error('Mermaid error: ' + e.message, e);
  }
}

const previewImageSrc = ref<PreviewImage|null>(null);
function showPreviewImage(event: MouseEvent) {
  const imgElement = event.target as HTMLImageElement;
  if (imgElement && imgElement.tagName === 'IMG' && imgElement.src) {
    const captionEl = imgElement.parentElement?.querySelector('figcaption');
    previewImageSrc.value = {
      src: imgElement.src,
      caption: captionEl?.innerText,
    }
    event.stopPropagation();
  }
}

onMounted(() => {
  previewRef.value?.addEventListener('click', showPreviewImage);

  postProcessRenderedHtml(); 
});
onUpdated(() => postProcessRenderedHtml());
onBeforeUnmount(() => {
  previewRef.value?.removeEventListener('click', showPreviewImage);
})
</script>

<style lang="scss" scoped>
@use "@/assets/vuetify.scss" as vuetify;

.preview {
  overflow: auto;
  word-wrap: break-word;
  padding: 0.5em;
}

.preview > :deep(*:first-child) {
  margin-top: 0;
}

.preview :deep() {
  @import "@/assets/rendering/base-text.scss";

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
