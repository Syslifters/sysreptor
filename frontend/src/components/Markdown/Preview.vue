<template>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <div ref="previewRef" v-html="renderedMarkdown" class="preview" />
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

  return absoluteApiUrl(props.rewriteFileUrl(`${imgSrc}?c=${cacheBuster}`));
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
  const mermaidNodes = previewRef.value!.querySelectorAll('.preview div.mermaid-diagram');
  try {
    await mermaid.run({ nodes: mermaidNodes });
  } catch (e: any) {
    // eslint-disable-next-line no-console
    console.error('Mermaid error: ' + e.message, e);
  }
}

onMounted(postProcessRenderedHtml);
onUpdated(postProcessRenderedHtml);
</script>

<style lang="scss" scoped>
@use "@/assets/vuetify.scss" as vuetify;

.preview {
  overflow: auto;
  word-wrap: break-word;
}

.preview > :deep(*:first-child) {
  margin-top: 0;
}

.preview :deep() {
  @import "@/assets/rendering/base-text.scss";

  .footnotes {
    border-top: 1px solid black;
    margin-top: 2em;

    h4 {
      font-size: 1em;
    }
    .data-footnote-backref {
      display: none;
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
