<template>
  <div>
    <!-- Rendered markdown gets sanitized in renderMarkdownToHtml -->
    <!-- eslint-disable-next-line vue/no-v-html -->
    <div v-if="isRendered" ref="previewRef" v-html="renderedMarkdown" @click.stop class="preview" />
    <div v-else class="preview preview-placeholder">
      <!-- Placeholder of raw text while markdown is initially rendered -->
      <p>{{ props.value }}</p>
    </div>
    <markdown-image-preview-dialog
      ref="previewDialogRef"
      v-model="previewImageSrc"
      :images="previewImagesAll"
      :readonly="props.readonly"
      :upload-file="props.uploadFile"
      :rewrite-file-url-map="props.rewriteFileUrlMap"
      @image-edited="emit('image-edited', $event)"
    />
  </div>
</template>

<script lang="ts">
import { mermaid } from '@sysreptor/markdown';
import { uuidv4 } from "@base/utils/helpers";
import { renderMarkdownToHtmlInWorker, type ReferenceItem } from '~/composables/markdown';
import 'highlight.js/styles/default.css';
import 'katex/dist/katex.min.css';

mermaid.initialize({
  startOnLoad: false,
  theme: 'neutral',
  securityLevel: 'strict',
});
</script>

<script setup lang="ts">
const props = defineProps<{
  value?: string|null;
  readonly?: boolean;
  rewriteFileUrlMap?: Record<string, string>;
  referenceItems?: ReferenceItem[];
  cacheBuster?: string;
  throttleMs?: number;
  uploadFile?: (file: File, body?: Record<string, any>) => Promise<string>;
}>();
const emit = defineEmits<{
  'rendered': [];
  'image-edited': [value: { oldUrl: string; newUrl: string }];
}>();

const cacheBusterFallback = uuidv4();
const cacheBuster = computed(() => props.cacheBuster || cacheBusterFallback);
const renderedMarkdown = ref('');
const renderedMarkdownText = ref('');
const isRendered = ref(false);
const throttleMs = computed(() => props.throttleMs ?? 500);
const abortController = shallowRef(new AbortController());
watchThrottled(() => props.value, async () => {
  try {
    const mdText = props.value || '';
    renderedMarkdown.value = await renderMarkdownToHtmlInWorker({
      text: mdText,
      preview: true,
      referenceItems: toRaw(props.referenceItems),
      rewriteFileUrlMap: props.rewriteFileUrlMap,
      cacheBuster: cacheBuster.value,
    }, { signal: abortController.value.signal });
    renderedMarkdownText.value = mdText;
    isRendered.value = true;

    await nextTick();
    postProcessRenderedHtml();
  } catch (error: any) {
    if (error?.name === 'AbortError') {
      return;
    }
    // eslint-disable-next-line no-console
    console.error('Markdown rendering error', { error });
  }
}, { throttle: throttleMs, leading: true, immediate: true });
onUnmounted(() => abortController.value.abort());

const previewRef = useTemplateRef('previewRef');
const previewDialogRef = useTemplateRef('previewDialogRef');

const previewImageSrc = ref<PreviewImage|null>(null);
const previewImagesAll = ref<PreviewImage[]>([]);
function getPreviewImagesAndSelected(clickedImg: HTMLImageElement | null): { images: PreviewImage[]; selected: PreviewImage | null } {
  if (!previewRef.value) {
    return { images: [], selected: null };
  }
  const images = Array.from(previewRef.value.querySelectorAll<HTMLImageElement>('img')).map((img: HTMLImageElement) => {
    const figureEl = img.parentElement?.classList.contains('preview-image-wrapper') ? img.parentElement.parentElement : img.parentElement;
    const captionEl = figureEl?.querySelector('figcaption');
    let markdown: string | undefined;
    try {
      const position = JSON.parse(figureEl?.getAttribute('data-position') || '');
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
  const selected = clickedImg ? images.find(img => img.src === clickedImg.src) ?? null : null;
  return { images, selected };
}
function openImageDialog(img: HTMLImageElement, editMode?: boolean) {
  const { images, selected } = getPreviewImagesAndSelected(img);
  if (selected) {
    previewImagesAll.value = images;
    previewDialogRef.value?.open?.(selected, editMode);
  }
}
useEventListener(previewRef, 'click', (e) => {
  const img = e.target as HTMLImageElement;
  if (img.tagName !== 'IMG' || !img.src) {
    return;
  }
  e.stopPropagation();
  openImageDialog(img);
});

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

  // Wrap all images, inject edit buttons
  const canEdit = !!props.uploadFile && !props.readonly;
  previewRef.value.querySelectorAll<HTMLImageElement>('figure > img').forEach((img) => {
    const figure = img.parentElement?.tagName === 'FIGURE' ? img.parentElement as HTMLElement : null;
    if (figure && canEdit) {
      const wrapper = document.createElement('span');
      wrapper.className = 'preview-image-wrapper';
      img.parentNode!.insertBefore(wrapper, img);
      wrapper.appendChild(img);

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.classList.add('preview-image-edit-btn', 'v-btn', 'v-btn--icon', 'v-btn--density-compact');
      const icon = document.createElement('i');
      icon.className = 'mdi mdi-image-edit-outline v-icon v-icon--size-small';
      btn.appendChild(icon);
      wrapper.appendChild(btn);

      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        openImageDialog(img, true);
      });
    }
  });

  // Render mermaid diagrams
  const mermaidNodes = previewRef.value.querySelectorAll<HTMLElement>('.preview div.mermaid-diagram');
  try {
    await mermaid.run({ nodes: mermaidNodes });
  } catch (e: any) {
    // eslint-disable-next-line no-console
    console.error('Mermaid error: ' + e.message, e);
  }

  emit('rendered');
}
whenever(previewRef, postProcessRenderedHtml, { immediate: true });

defineExpose({
  element: previewRef,
});
</script>

<style lang="scss" scoped>
@use "sass:meta";
@use "@base/assets/vuetify.scss" as vuetify;

.preview {
  overflow: auto;
  word-wrap: break-word;
  padding: 4px 0.5em;
}

.preview-placeholder {
  white-space: pre-wrap;
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
    background-color: color-mix(in srgb, rgb(var(--v-theme-on-surface)) 5%, transparent);
    border-left: 5px solid color-mix(in srgb, rgb(var(--v-theme-on-surface)) 30%, transparent);
  }
  table, th, td {
    border-color: rgb(var(--v-border-color));
  }

  figure img {
    cursor: zoom-in;
  }

  .preview-image-wrapper {
    display: inline-block;
    position: relative;

    &:hover .preview-image-edit-btn {
      opacity: 1;
    }

    .preview-image-edit-btn {
      position: absolute;
      top: 0.25rem;
      right: 0.25rem;
      width: 2rem;
      height: 2rem;

      border-radius: 4px;
      opacity: 0;
      transition: opacity 0.15s ease;
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

  .mermaid-diagram svg {
    width: 100%;
    max-width: 100% !important;
  }
}
</style>
