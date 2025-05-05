<template>
  <div ref="mdeRef" class="mde" :class="'mde-mode-' + props.markdownEditorMode">
    <markdown-toolbar 
      ref="toolbarRef"
      class="mde-toolbar"
      v-bind="markdownToolbarAttrs"
    />
    <teleport 
      v-if="toolbarRef && $slots['context-menu']" 
      :to="`#${toolbarRef!.additionalContentId}`" 
      defer
    >
      <!-- 
        Context menu for the markdown-toolbar.
        Use teleport instead of slots to improve render performance.
        When slots are defined inside <markdown-toolbar> drastically increase render time, even when not actually rendered (behind a v-if).
      -->
      <markdown-toolbar-context-menu>
        <template #default><slot name="context-menu" :disabled="markdownToolbarAttrs.disabled" /></template>
      </markdown-toolbar-context-menu>
    </teleport>

    <div class="mde-container-editor">
      <div
        ref="editorRef"
        v-intersect="onIntersect"
        class="mde-editor"
      />
    </div>
    <v-divider vertical class="mde-separator" />
    <div ref="previewContainerRef" class="mde-container-preview">
      <div class="mde-scrollspacer" :style="{height: `${scrollSpacerTop}px`}" />
      <markdown-preview 
        v-if="props.markdownEditorMode !== MarkdownEditorMode.MARKDOWN"
        ref="previewRef"
        v-bind="markdownPreviewAttrs" 
        class="mde-preview"
      />
      <div class="mde-scrollspacer" :style="{height: `${scrollSpacerBottom}px`}" />
    </div>

    <div class="mde-footer">
      <v-divider />
      <markdown-statusbar v-if="editorView" v-bind="markdownStatusbarAttrs" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { sortBy, throttle } from 'lodash-es';
import type { MarkdownToolbar } from '#components';
import { MarkdownEditorMode } from '#imports';

const props = defineProps(makeMarkdownProps());
const emit = defineEmits(makeMarkdownEmits());

const { editorView, markdownToolbarAttrs, markdownStatusbarAttrs, markdownPreviewAttrs, onIntersect, focus, blur } = useMarkdownEditor({
  props: computed(() => ({ ...props, spellcheckSupported: true } as any)),
  emit,
  extensions: markdownEditorDefaultExtensions(),
  fileUploadSupported: true,
});

const toolbarRef = useTemplateRef<InstanceType<typeof MarkdownToolbar>>('toolbarRef');


const mdeRef = useTemplateRef('mdeRef');
const previewRef = useTemplateRef('previewRef');
const previewContainerRef = useTemplateRef('previewContainerRef');
const scrollParentEditor = computed(() => {
  if (props.markdownEditorMode !== MarkdownEditorMode.MARKDOWN_AND_PREVIEW) {
    return undefined;
  }
  return getScrollParent(mdeRef.value) || undefined;
});

const scrollSpacerTop = ref(0);
const scrollSpacerBottom = ref(0);
async function syncScrollEditorToPreview() {
  if (!mdeRef.value || !editorView.value || !editorView.value.contentDOM || !toolbarRef.value?.$el || !previewRef.value?.element || !previewContainerRef.value) {
    return;
  }
  
  // Check if mdeRef is in viewport
  const rect = mdeRef.value?.getBoundingClientRect();
  if (rect.bottom < 0 || rect.top > window.innerHeight) { return; }

  // Get first visible codemirror line
  const codemirrorLine = Array.from(editorView.value.contentDOM.querySelectorAll<HTMLElement>(':scope > .cm-line')).find(isVisible);
  if (!codemirrorLine) { return; }

  // Get corresponding preview element for codemirror line
  const lineNumber = editorView.value.state.doc.lineAt(editorView.value.posAtCoords(codemirrorLine.getBoundingClientRect(), false)).number;
  const previewElement = getPreviewElementForLine(lineNumber);
  if (!previewElement) { return; }

  // previewElementOffsetTop and codemirrorLineOffsetTop should be at the same level (they are the same line/block).
  // Both offsets are relative to the same DOM position: mdeRef below the toolbar.
  // So we need to scroll previewContainerRef to the difference between the two offsets (when height(preview) > height(codemirror)).
  const previewElementOffsetTop = getOffsetTop(previewElement, previewContainerRef.value) - scrollSpacerTop.value;
  const codemirrorLineOffsetTop = codemirrorLine.offsetTop;
  let newScrollTop = previewElementOffsetTop - codemirrorLineOffsetTop
  let newSpacerTop = 0;
  let newSpacerBottom = 0;

  if (newScrollTop < 0) {
    newSpacerTop = newScrollTop * -1;
    newScrollTop = 0;
  } else {
    // newScrollTop -= scrollSpacerTop.value;
    newSpacerTop = 0;
  }

  const maxScrollTop = previewContainerRef.value.scrollHeight - previewContainerRef.value.clientHeight - scrollSpacerBottom.value - scrollSpacerTop.value + newSpacerTop;
  if (newScrollTop > maxScrollTop) {
    newSpacerBottom = newScrollTop - maxScrollTop;
  } else {
    newSpacerBottom = 0;
  }

  // console.log('scrollSpacerTop', scrollSpacerTop.value, 'scrollSpacerBottom', scrollSpacerBottom.value);
  console.log('newScrollTop', newScrollTop, 'maxScrollTop', maxScrollTop, 'scrollSpacerBottom', scrollSpacerBottom.value, 'scrollSpacerTop', scrollSpacerTop.value);
  scrollSpacerTop.value = newSpacerTop;
  scrollSpacerBottom.value = newSpacerBottom;  
  await nextTick();
  // console.log('scrollSpacers', Array.from(previewContainerRef.value.children).map(el => el.clientHeight));

  previewContainerRef.value!.scrollTo({ 
    top: newScrollTop,
    behavior: 'smooth' 
  });

}
useEventListener(scrollParentEditor, 'scroll', throttle(syncScrollEditorToPreview, 200));
watch([() => props.markdownEditorMode, scrollParentEditor, editorView, previewRef], syncScrollEditorToPreview);


function isVisible(el: Element) {
  const elRect = el.getBoundingClientRect()
  const editorOffsetTop = toolbarRef.value!.$el.getBoundingClientRect().bottom;
  const bottomVisible = elRect.bottom - editorOffsetTop;
  return bottomVisible > 0 && elRect.top < window.innerHeight;
}
function getPosition(el?: Element|null): {start: {line: number, offset: number}, end: {line: number, offset: number}}|null {
  if (!el) {
    return null;
  }
  try {
    const position = JSON.parse(el.getAttribute('data-position') || '');
    if (position && Number.isInteger(position?.start?.line)) {
      return position;
    }
  } catch { 
    // Ignore error
  }
  return null;
}
function getDepth(el: Element): number {
  let depth = 0;
  while (el && el.parentElement) {
    depth++;
    el = el.parentElement;
  }
  return depth;
}
function getOffsetTop(el: HTMLElement, offsetParent: HTMLElement): number {
  let offsetTop = el.offsetTop;
  while (el.offsetParent && el.offsetParent !== offsetParent) {
    el = el.offsetParent as HTMLElement
    offsetTop += el.offsetTop;
  }
  return offsetTop;
}
function getPreviewElementForLine(lineNumber: number): HTMLElement|null {
  if (!previewRef.value?.element) {
    return null;
  }
  const previewElements = Array.from(previewRef.value.element.querySelectorAll<HTMLElement>('[data-position]'))
    .filter(el => {
      const position = getPosition(el);
      return position && lineNumber >= position.start.line && lineNumber <= position.end.line
    });
  // Get the deepest element for this line (e.g. table->tr, ul->li)
  const previewElement = sortBy(previewElements.map(el => ({ el, depth: getDepth(el) * -1})), ['depth'])[0]?.el;
  return previewElement || null;
}

defineExpose({
  focus,
  blur,
});
</script>

<style lang="scss" scoped>
@use "sass:meta";

$mde-min-height: 15em;


.mde {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  grid-template-rows: auto 1fr auto;
  grid-template-areas: 
    "toolbar toolbar toolbar"
    "editor separator preview"
    "footer footer footer";
  gap: 0;
  align-items: start;
  width: 100%;
}

.mde-toolbar { grid-area: toolbar; }
.mde-footer { grid-area: footer; }
.mde-separator { grid-area: separator; }
.mde-container-editor { grid-area: editor; }
.mde-container-preview { grid-area: preview; }

.mde-mode-markdown {
  .mde-separator, .mde-container-preview {
    display: none;
  }
  .mde-container-editor {
    grid-column: editor / span preview;
  }
}
.mde-mode-preview {
  .mde-container-editor, .mde-separator, .mde-scrollspacer {
    display: none;
  }
  .mde-container-preview {
    grid-column: editor / span preview;
    min-height: $mde-min-height;
  }
}
.mde-mode-markdown-preview {
  .mde-container-editor { grid-area: editor; }
  .mde-container-preview { grid-area: preview; }
  .mde-container-preview {
    min-height: 100%;
    height: 0;
    overflow-y: auto;
    scrollbar-width: none;
    position: relative;
  }
}

.mde-scrollspacer {
  transition: height 0.1s;
}

:deep(.mde-editor) {
  @include meta.load-css("@/assets/mde-highlight.scss");

  /* set min-height, grow when lines overflow */
  .cm-editor { height: 100%; }
  .cm-content, .cm-gutter { min-height: $mde-min-height; }
  .cm-scroller { overflow: auto; }
  .cm-wrap { border: 1px solid silver }
}
</style>


<!-- TODO: sync scroll
* [ ] sync scroll editor to preview
* [ ] sync scroll preview to editor
* [ ] handle height(codemirror) < height(preview)
  * scroll in preview
* [x] handle height(codemirror) > height(preview)
  * negative scroll not allowed in browsers
  * maybe add spacers at start/end of preview ???
* [ ] prevent scroll feedback loop
  * programmatic scroll sync in one pane should not trigger scroll event in other pane
* [ ] sync position of MD blocks (codemirror syntax tree) instead of lines
* [ ] be less strict with syncing scroll position
  * do not only regard the first visible line
  * also regard other lines
  * only sync scroll when no visible codemirror line is in preview ???
-->
