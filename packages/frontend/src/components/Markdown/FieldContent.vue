<template>
  <div class="mde" :class="'mde-mode-' + props.markdownEditorMode">
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
      <div v-if="spacerHeight > 0" class="mde-spacer">
        <div class="mde-endmarker mde-endmarker-top">
          <s-btn
            @click="syncScrollOrTop()"
            text="End of preview"
            append-icon="mdi-arrow-down"
            variant="plain"
          />
        </div>
      </div>
      <markdown-preview 
        v-if="props.markdownEditorMode !== MarkdownEditorMode.MARKDOWN"
        ref="previewRef"
        v-bind="markdownPreviewAttrs" 
        class="mde-preview"
      />
      <div v-if="spacerHeight > 0" class="mde-spacer">
        <v-spacer />
        <div class="mde-endmarker mde-endmarker-bottom">
          <s-btn
            @click="syncScrollOrTop()"
            text="End of preview"
            append-icon="mdi-arrow-up"
            variant="plain"
          />
        </div>
      </div>
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
import { EditorView, syntaxTree, type ViewUpdate, type SyntaxNode } from '@sysreptor/markdown/editor';

const props = defineProps(makeMarkdownProps());
const emit = defineEmits(makeMarkdownEmits());

const { editorView, markdownToolbarAttrs, markdownStatusbarAttrs, markdownPreviewAttrs, onIntersect, focus, blur } = useMarkdownEditor({
  props: computed(() => ({ ...props, spellcheckSupported: true } as any)),
  emit,
  extensions: [
    ...markdownEditorDefaultExtensions(),
    EditorView.updateListener.of(onEditorUpdate),
  ],
  fileUploadSupported: true,
});

const toolbarRef = useTemplateRef<InstanceType<typeof MarkdownToolbar>>('toolbarRef');


// Sync scroll
const editorRef = ref<HTMLDivElement>();
const previewRef = useTemplateRef('previewRef');
const previewContainerRef = useTemplateRef('previewContainerRef');
const scrollParentEditor = computed(() => {
  if (props.markdownEditorMode !== MarkdownEditorMode.MARKDOWN_AND_PREVIEW) {
    return undefined;
  }
  return getScrollParent(editorRef.value) || undefined;
});

const previewMinHeight = ref(0);
const spacerHeight = ref(0);
const endmarkerTopOffset = ref(0);
const endmarkerBottomOffset = ref(0);
function syncScrollEditorToPreview() {
  if (!editorRef.value || !editorView.value || !editorView.value.contentDOM || !toolbarRef.value?.$el || !previewRef.value?.element || !previewContainerRef.value) {
    return false;
  }

  // Check if editorRef is in viewport
  const rect = editorRef.value?.getBoundingClientRect();
  if (rect.bottom < 0 || rect.top > window.innerHeight) { return false; }

  // Set offset of preview end markers
  // We need to calculate the offset in JS because the field might be larger than the viewport.
  // If the top/bottom is outside the viewport, we need to add an offset such that the markers stay visible.
  endmarkerTopOffset.value = Math.max(0, (rect.top - toolbarRef.value.$el.getBoundingClientRect().bottom) * -1);
  endmarkerBottomOffset.value = Math.max(0, rect.bottom - window.innerHeight);

  // Get editor line to sync preview to
  let editorLine = undefined as HTMLElement|undefined;
  if (props.isFocussed || props.isFocussed === undefined) {
    // Use the cursor position if the field is focused and the cursor is visible
    const cursorLine = getEditorLineForPosition(editorView.value.state.selection.main.head);
    if (cursorLine && isVisible(cursorLine, 0)) {
      editorLine = cursorLine;
    }
  }
  if (!editorLine) {
    // Fallback to the first visible line if the cursor is not visible (e.g. out of viewport)
    editorLine = Array.from(editorView.value.contentDOM.querySelectorAll<HTMLElement>(':scope > .cm-line')).find(isVisible);
  }
  const mdBlock = getEditorMarkdownBlockForLine(editorLine);
  if (!mdBlock) { return false; }

  // Get corresponding preview element for codemirror line
  const previewElement = getPreviewElementForLine(mdBlock?.line.number);
  if (!previewElement) { return false; }

  // previewElementOffsetTop and mdBlockOffsetTop should be at the same level (they are the same line/block).
  // Both offsets are relative to the same DOM position: inside the field below the toolbar.
  // So we need to scroll previewContainerRef to the difference between the two offsets (when height(preview) > height(codemirror)).
  const previewElementOffsetTop = getOffsetTop(previewElement, previewContainerRef.value);
  const mdBlockOffsetTop = mdBlock.element.offsetTop;
  const newScrollTop = previewElementOffsetTop - mdBlockOffsetTop;

  if (Math.abs(newScrollTop - previewContainerRef.value.scrollTop) < 1) {
    // We are already at the desired position. No need to scroll.
    return true;
  }

  // Scroll to the new position
  previewContainerRef.value.scrollTo({ 
    top: newScrollTop,
    behavior: 'smooth', 
  });
  return true;
}
function syncScrollOrTop() {
  const success = syncScrollEditorToPreview();
  if (!success && previewContainerRef.value && previewRef.value?.element && toolbarRef.value?.$el) {
    // scroll to start of preview
    const newScrollTop = 0 + previewRef.value.element.offsetTop + previewContainerRef.value.getBoundingClientRect().top - toolbarRef.value.$el.getBoundingClientRect().bottom;
    previewContainerRef.value.scrollTo({
      top: newScrollTop,
      behavior: 'smooth',
    });
  }
}

async function updateSpacers() {
  if (props.markdownEditorMode !== MarkdownEditorMode.MARKDOWN_AND_PREVIEW || !previewContainerRef.value || !previewRef.value?.element || !editorRef.value) {
    previewMinHeight.value = 0;
    spacerHeight.value = 0;
    return;
  }

  const oldSpacerHeight = spacerHeight.value;
  const oldScrollTop = previewContainerRef.value.scrollTop;

  // Ensure that spacers are large enough to allow scrolling to every preview block for every editor position.
  previewMinHeight.value = Math.min(previewRef.value.element.clientHeight, window.innerHeight);
  if (previewRef.value.element.clientHeight <= editorRef.value.clientHeight && editorRef.value.clientHeight < window.innerHeight * 0.9) {
    // Disable scrolling for small fields in preview if preview fully fits in the editor area and on the screen
    spacerHeight.value = 0;
  } else {
    spacerHeight.value = Math.max(previewRef.value.element.clientHeight, editorRef.value.clientHeight * 2);
  }

  // correct scrollTop by the same amount as spacerHeight to prevent jumping
  // 1px offset to prevent scrolling when preview content is initially rendered
  await nextTick();
  previewContainerRef.value.scrollTop = Math.max(0, oldScrollTop - oldSpacerHeight + spacerHeight.value - 1);
}

async function onEditorUpdate(update: ViewUpdate) {
  if (props.markdownEditorMode !== MarkdownEditorMode.MARKDOWN_AND_PREVIEW) {
    return;
  }
  if (!(update.docChanged || update.selectionSet)) {
    return;
  }
  await nextTick();
  // Note: The preview might not be rendered yet. 
  // New markdown blocks (e.g. when typing the first characters) might not have a corresponding preview element.
  // On following view updates (e.g. typing more characters), the preview element will be availalbe and scrolled to.
  syncScrollEditorToPreview();
}

useEventListener(scrollParentEditor, 'scroll', throttle(syncScrollEditorToPreview, 200, { leading: false, trailing: true }), { passive: true });
watch([() => props.markdownEditorMode, scrollParentEditor, editorView, () => previewRef.value?.element], async () => {
  await updateSpacers();
  syncScrollEditorToPreview();
}, { immediate: true });
useResizeObserver([() => previewRef.value?.element, editorRef.value], updateSpacers);


function isVisible(el: Element, threshold = 30) {
  const elRect = el.getBoundingClientRect()
  const editorOffsetTop = toolbarRef.value!.$el.getBoundingClientRect().bottom;
  const bottomVisible = elRect.bottom - editorOffsetTop;
  // At least threshold px of the element are visible
  return bottomVisible > threshold && elRect.top < window.innerHeight;
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
function getEditorMarkdownBlockForLine(codemirrorLine?: HTMLElement) {
  if (!codemirrorLine || !editorView.value) {
    return null;
  }

  const pos = editorView.value.posAtCoords(codemirrorLine.getBoundingClientRect(), false);

  // Get syntax tree node for current markdown block.
  // Use the sub-block (instead of top-level block) for nested elements (listItem, tableRow)
  const tree = syntaxTree(editorView.value.state);
  let node = tree.resolve(pos + 1, 1) as SyntaxNode|null;
  while (node && !['content', 'document'].includes(node.parent?.name as string) && !['listItem', 'tableRow', 'image'].includes(node.type.name)) {
    node = node.parent;
  }
  if (!node || ['content', 'document', ''].includes(node?.name as string)) {
    return null;
  }

  const position = node.from;
  const line = editorView.value.state.doc.lineAt(position);
  const element = getEditorLineForPosition(position);
  if (!element) {
    return null;
  }

  return {
    line,
    position,
    element
  }
}
function getEditorLineForPosition(position: number): HTMLElement|null {
  return (editorView.value as any)?.docView?.children
    ?.find((c: any) => c.posAtStart <= position && position <= c.posAtEnd && c.dom?.classList.contains('cm-line'))
    ?.dom || null;
}

function getPreviewElementForLine(lineNumber?: number): HTMLElement|null {
  if (!Number.isInteger(lineNumber) || !previewRef.value?.element) {
    return null;
  }
  const previewElements = Array.from(previewRef.value.element.querySelectorAll<HTMLElement>('[data-position]'))
    .filter(el => {
      const position = getPosition(el);
      return position && lineNumber! >= position.start.line && lineNumber! <= position.end.line;
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

.mde {
  --mde-min-height: max(18em, calc(v-bind(previewMinHeight) * 1px));

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
  .mde-container-editor, .mde-separator, .mde-spacer {
    display: none;
  }
  .mde-container-preview {
    grid-column: editor / span preview;
  }
  .mde-preview {
    min-height: var(--mde-min-height);
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
    overscroll-behavior-y: contain;
    position: relative;
  }
  .mde-spacer {
    height: calc(v-bind(spacerHeight) * 1px);
    display: flex;
    flex-direction: column;
  }
  .mde-endmarker {
    position: sticky;
    text-align: center;

    .v-btn {
      text-transform: none;
      font-style: italic;
    }

    &-top {
      top: calc(v-bind(endmarkerTopOffset) * 1px);
      padding-bottom: 100vh;
      padding-top: 5em;
    }
    &-bottom {
      bottom: calc(v-bind(endmarkerBottomOffset) * 1px);
      padding-top: 100vh;
      padding-bottom: 5em;
    }

  }
}


:deep(.mde-editor) {
  @include meta.load-css("@/assets/mde-highlight.scss");

  /* set min-height, grow when lines overflow */
  .cm-editor { height: 100%; }
  .cm-content, .cm-gutter { min-height: var(--mde-min-height); }
  .cm-scroller { overflow: auto; }
  .cm-wrap { border: 1px solid silver }
}
</style>
