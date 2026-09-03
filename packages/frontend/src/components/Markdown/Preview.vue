<template>
  <div ref="hostRef" class="preview-host" @click.stop>
    <!-- 
      allow-scripts omitted on purpose; 
      "Blocked script execution in about:srcdoc" console errors are from browser extensions 
      trying to inject scripts, not app content 
    -->
    <iframe
      v-show="isRendered"
      ref="iframeRef"
      :srcdoc="IFRAME_SRCDOC"
      sandbox="allow-same-origin allow-downloads allow-popups allow-popups-to-escape-sandbox"
      referrerpolicy="no-referrer"
      title="Markdown preview"
      class="preview-iframe"
      :style="{
        colorScheme: theme.current.value.dark ? 'dark' : 'light',
      }"
      @load="onIframeLoad"
    />
    <div v-show="!isRendered" class="preview preview-placeholder">
      <!-- Placeholder of raw text while markdown is initially rendered -->
      <p>{{ props.value }}</p>
    </div>

    <!-- Download options, shown when right-clicking a file download link -->
    <v-menu
      v-model="fileDownloadMenu.visible"
      :target="[fileDownloadMenu.x, fileDownloadMenu.y]"
    >
      <v-list density="compact" data-testid="file-download-menu">
        <v-list-item
          @click="downloadFile()"
          prepend-icon="mdi-download"
          title="Download"
          data-testid="file-download-plain"
        />
        <v-list-item
          @click="downloadFileEncryptedChannel()"
          prepend-icon="mdi-shield-lock-outline"
          title="Download via encrypted channel"
          subtitle="Prevents proxies from inspecting the download"
          data-testid="file-download-encrypted"
        />
      </v-list>
    </v-menu>
  </div>
</template>

<script lang="ts">
import { mermaid } from '@sysreptor/markdown';
import type { ChangeSpec } from '@sysreptor/markdown/editor';
import { uuidv4 } from "@base/utils/helpers";
import { downloadFileEncrypted } from "@base/utils/download";
import { renderMarkdownToHtmlInWorker, type ReferenceItem } from '~/composables/markdown';

import baseTextCss from '@/assets/rendering/base-text.css?inline';
import notoCss from '@base/assets/fonts/noto/noto.css?inline';
import mdiCss from '@mdi/font/css/materialdesignicons.css?inline';
import previewCss from './preview.scss?inline';

mermaid.initialize({
  startOnLoad: false,
  theme: 'neutral',
  securityLevel: 'strict',
  htmlLabels: false,
});

const IFRAME_SRCDOC = '<!DOCTYPE html><html><head><meta charset="utf-8"></head><body><div id="preview-content"></div></body></html>';
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
  'open-image-dialog': [value: { selected: PreviewImage; images: PreviewImage[]; editMode?: boolean }];
  'change': [value: ChangeSpec];
}>();

const theme = useVTheme();

const cacheBusterFallback = uuidv4();
const cacheBuster = computed(() => props.cacheBuster || cacheBusterFallback);
const renderedMarkdown = ref('');
const renderedMarkdownText = ref('');
const isRendered = ref(false);
const iframeReady = ref(false);
const throttleMs = computed(() => props.throttleMs ?? 500);
const abortController = shallowRef(new AbortController());

const hostRef = useTemplateRef('hostRef');
const iframeRef = useTemplateRef<HTMLIFrameElement>('iframeRef');

let contentResizeObserver: ResizeObserver | null = null;
const mermaidSvgCache = new Map<string, string>();

function previewContent() {
  return iframeRef.value?.contentDocument?.getElementById('preview-content') ?? null;
}

function setIframeStyle(id: string, css: string) {
  const doc = iframeRef.value?.contentDocument;
  if (!doc) {
    return;
  }

  let el = doc.head.querySelector(`head style#${CSS.escape(id)}`) as HTMLStyleElement | null;
  if (!el) {
    el = doc.createElement('style');
    el.id = id;
    doc.head.appendChild(el);
  }
  if (el.textContent !== css) {
    el.textContent = css;
  }
}

function syncIframeStyles() {
  const doc = iframeRef.value?.contentDocument;
  if (!doc || !iframeReady.value) {
    return;
  }

  setIframeStyle('md-preview-theme', theme.styles.value);
  if (hostRef.value) {
    const s = getComputedStyle(hostRef.value);
    setIframeStyle('md-preview-host', `
    body.preview {
      font-size: ${s.fontSize};
      line-height: ${s.lineHeight};
    }`);
  }

  doc.documentElement.className = theme.themeClasses.value || '';
  doc.body.classList.add('preview');
}

function updateIframeHeight() {
  const iframe = iframeRef.value;
  const content = previewContent();
  const body = iframe?.contentDocument?.body;
  if (!iframe || !content || !body) {
    return;
  }
  const bodyStyle = content.ownerDocument.defaultView?.getComputedStyle(body);
  const paddingY = bodyStyle
    ? (parseFloat(bodyStyle.paddingTop) || 0) + (parseFloat(bodyStyle.paddingBottom) || 0)
    : 0;
  iframe.style.height = `${Math.ceil(Math.max(content.scrollHeight, content.offsetHeight) + paddingY) + 10}px`;
}

function onIframeLoad() {
  const doc = iframeRef.value?.contentDocument;
  const content = previewContent();
  if (!doc || !content) {
    return;
  }

  setIframeStyle('md-preview-static', [
    notoCss, 
    mdiCss, 
    baseTextCss, 
    previewCss,
  ].join('\n'));

  contentResizeObserver?.disconnect();
  contentResizeObserver = new ResizeObserver(updateIframeHeight);
  contentResizeObserver.observe(content);

  // Handle events from the parent (iframe has no scripts)
  doc.body.addEventListener('click', handlePreviewClick as EventListener);
  doc.body.addEventListener('contextmenu', handlePreviewContextMenu as EventListener);
  iframeReady.value = true;
  syncIframeStyles();
  if (isRendered.value) {
    writeContentAndPostProcess();
  }
}

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
    if (iframeReady.value) {
      writeContentAndPostProcess();
    }
  } catch (error: any) {
    if (error?.name === 'AbortError') {
      return;
    }
    // eslint-disable-next-line no-console
    console.error('Markdown rendering error', { error });
  }
}, { throttle: throttleMs, leading: true, immediate: true });

watch([theme.styles, theme.themeClasses], syncIframeStyles);

useResizeObserver(hostRef, () => {
  syncIframeStyles();
  updateIframeHeight();
});

onUnmounted(() => {
  abortController.value.abort();
  contentResizeObserver?.disconnect();
  contentResizeObserver = null;
});

function getPreviewImagesAndSelected(clickedImg: HTMLImageElement | null): { images: PreviewImage[]; selected: PreviewImage | null } {
  const content = previewContent();
  if (!content) {
    return { images: [], selected: null };
  }
  const images = Array.from(content.querySelectorAll<HTMLImageElement>('img')).map((img: HTMLImageElement) => {
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
    emit('open-image-dialog', { selected, images, editMode });
  }
}

function handlePreviewClick(e: MouseEvent) {
  const target = e.target as Element | null;
  if (!target) {
    return;
  }

  const anchor = target.closest?.('a') as HTMLAnchorElement | null;
  if (anchor) {
    const href = anchor.getAttribute('href');
    if (href?.startsWith('#')) {
      e.preventDefault();
      e.stopPropagation();
      anchor.ownerDocument.querySelector(href)?.scrollIntoView({ behavior: 'smooth' });
    }
  }

  const img = target.closest?.('img') as HTMLImageElement | null;
  if (img?.src) {
    e.stopPropagation();
    openImageDialog(img);
  }
}

const fileDownloadMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  href: null as string | null,
  download: null as string | null,
});
function handlePreviewContextMenu(e: MouseEvent) {
  const target = e.target as Element | null;
  const anchor = target?.closest?.('a.file-download-preview') as HTMLAnchorElement | null;
  if (!anchor || !iframeRef.value) {
    return;
  }

  e.preventDefault();
  e.stopPropagation();
  const iframeRect = iframeRef.value.getBoundingClientRect();
  fileDownloadMenu.value = {
    visible: true,
    x: iframeRect.left + e.clientX,
    y: iframeRect.top + e.clientY,
    href: anchor.href,
    download: anchor.getAttribute('download'),
  };
}
function downloadFile() {
  const { href, download } = fileDownloadMenu.value;
  if (!href) {
    return;
  }
  const a = document.createElement('a');
  a.href = href;
  if (download) {
    a.download = download;
  }
  a.target = '_blank';
  a.rel = 'nofollow noopener noreferrer';
  document.body.appendChild(a);
  a.click();
  a.remove();
}
async function downloadFileEncryptedChannel() {
  const { href, download } = fileDownloadMenu.value;
  if (!href) {
    return;
  }
  try {
    await downloadFileEncrypted(href, { filename: download });
  } catch (error: any) {
    requestErrorToast({ error, message: 'Download failed' });
  }
}


async function writeContentAndPostProcess() {
  const doc = iframeRef.value?.contentDocument;
  const content = previewContent();
  if (!doc || !content || !iframeReady.value) {
    return;
  }

  // Rendered markdown gets sanitized in renderMarkdownToHtml
  content.innerHTML = renderedMarkdown.value;

  // Wrap all images, inject edit buttons
  const canEditImages = !!props.uploadFile && !props.readonly;
  content.querySelectorAll<HTMLImageElement>('figure > img').forEach((img) => {
    const figure = img.parentElement?.tagName === 'FIGURE' ? img.parentElement as HTMLElement : null;
    if (figure && canEditImages) {
      const wrapper = doc.createElement('span');
      wrapper.className = 'preview-image-wrapper';
      img.parentNode!.insertBefore(wrapper, img);
      wrapper.appendChild(img);

      const btn = doc.createElement('button');
      btn.type = 'button';
      btn.classList.add('preview-image-edit-btn', 'v-btn', 'v-btn--icon', 'v-btn--density-compact');
      const icon = doc.createElement('i');
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

  // Inject copy buttons into code blocks
  content.querySelectorAll<HTMLPreElement>('pre.code-block:not(:has(.preview-code-copy-btn)):has(code)').forEach((pre) => {
    const btn = doc.createElement('button');
    btn.type = 'button';
    btn.classList.add('preview-code-copy-btn', 'v-btn', 'v-btn--icon', 'v-btn--density-compact');
    const icon = doc.createElement('i');
    icon.className = 'mdi mdi-content-copy v-icon v-icon--size-small';
    btn.appendChild(icon);
    pre.appendChild(btn);

    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      copyToClipboard(pre.querySelector('code')?.textContent || '');
    });
  });

  // Allow checking task list items by clicking on the checkbox
  if (!props.readonly) {
    content.querySelectorAll<HTMLInputElement>('li.task-list-item > input[type="checkbox"][disabled]').forEach((input) => {
      input.removeAttribute('disabled');
      input.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (props.readonly) { return; }

        try {
          const position = JSON.parse(input.parentElement?.getAttribute('data-position') || '');
          if (Number.isInteger(position?.start?.offset) && Number.isInteger(position?.end?.offset)) {
            // Ensure that the preview is up to date (not outdated due to throttled rendering => position or text might change)
            const markdown = renderedMarkdownText.value.substring(position.start.offset, position.end.offset) || '';
            const m = markdown.match(/\[.\]/);
            if (m && m[0] === props.value?.substring(position.start.offset + m.index, position.start.offset + m.index + m[0].length)) {
              // Update checkbox state markdown text and DOM (for immediate visual feedback)
              if (input.hasAttribute('checked')) {
                input.removeAttribute('checked');
                emit('change', {
                  from: position.start.offset + m.index,
                  to: position.start.offset + m.index + m[0].length,
                  insert: '[ ]',
                });
              } else {
                input.setAttribute('checked', 'checked');
                emit('change', {
                  from: position.start.offset + m.index,
                  to: position.start.offset + m.index + m[0].length,
                  insert: '[x]',
                });
              }
            }
          }
        } catch {
          return;
        }
      });
    });
  }

  // Render mermaid in the parent document, then inject SVG into the iframe.
  const mermaidNodes = Array.from(content.querySelectorAll<HTMLElement>('div.mermaid-diagram'));
  await renderMermaidDiagrams(mermaidNodes);

  updateIframeHeight();
  emit('rendered');
}

async function renderMermaidDiagrams(nodes: HTMLElement[]) {
  if (nodes.length === 0) {
    mermaidSvgCache.clear();
    return;
  }

  const width = Math.max(iframeRef.value?.clientWidth || 0, hostRef.value?.clientWidth || 0, 1);
  const host = document.createElement('div');
  host.style.position = 'absolute';
  host.style.left = '-99999px';
  host.style.top = '0';
  host.style.width = `${width}px`;
  host.style.visibility = 'hidden';
  host.style.pointerEvents = 'none';
  document.body.appendChild(host);

  const seenDefinitions = new Set<string>();
  try {
    for (const node of nodes) {
      const definition = node.textContent?.trim();
      if (!definition) {
        continue;
      }
      seenDefinitions.add(definition);

      let svg = mermaidSvgCache.get(definition);
      if (!svg) {
        const id = `mdmermaid${uuidv4().replace(/-/g, '')}`;
        try {
          ({ svg } = await mermaid.render(id, definition, host));
          mermaidSvgCache.set(definition, svg);
        } catch (e: any) {
          // eslint-disable-next-line no-console
          console.error('Mermaid error: ' + e.message, e);
        } finally {
          document.getElementById(id)?.remove();
          document.getElementById(`d${id}`)?.remove();
          host.replaceChildren();
        }
      }
      if (svg) {
        node.innerHTML = svg;
      }
    }
  } finally {
    host.remove();
  }

  for (const key of mermaidSvgCache.keys()) {
    if (!seenDefinitions.has(key)) {
      mermaidSvgCache.delete(key);
    }
  }
}

defineExpose({
  element: iframeRef,
});
</script>

<style lang="scss" scoped>
.preview-host {
  width: 100%;
}

.preview-iframe {
  display: block;
  width: 100%;
  border: 0;
  overflow: hidden;
  background: transparent;
  // Avoid flash of short iframe before auto-height
  min-height: 1em;
}

.preview-placeholder {
  overflow: auto;
  word-wrap: break-word;
  padding: 4px 0.5em;
  white-space: pre-wrap;
}
</style>
