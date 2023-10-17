<template>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <div ref="previewRef" v-html="renderedMarkdown" class="preview" />
</template>

<script setup lang="ts">
import { v4 as uuidv4 } from 'uuid';
import throttle from 'lodash/throttle';
// @ts-ignore
import { renderMarkdownToHtml } from 'reportcreator-markdown';
import { absoluteApiUrl } from '~/utils/urls';

const props = defineProps<{
  value?: string|null;
  rewriteFileUrl?: (fileSrc: string) => string;
  rewriteReferenceLink?: (src: string) => {href: string, title: string}|null;
}>();

const renderedMarkdown = ref('');
const cacheBuster = uuidv4();

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
onUpdated(() => {
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
})
</script>

<style lang="scss" scoped>
.preview {
  overflow: auto;
  word-wrap: break-word;
  background-color: #fafafa;
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
}
</style>
