<template>
  <div
    ref="wrapperRef"
    class="resizable-drawer-wrapper"
    :class="{ 'resizing': isDragging, 'collapsed': isCollapsed }"
  >
    <div 
      class="resizable-drawer"
      :style="{ width: `${displayWidth}px` }"
    >
      <div class="resizable-drawer__content">
        <slot />
      </div>
    </div>
    
    <!-- Resize handle -->
    <div
      class="resize-handle"
      :class="{ 
        'resize-handle--left': handleLocation === 'left', 
        'resize-handle--right': handleLocation === 'right',
        'resize-handle--active': isDragging
      }"
      @mousedown="startResize"
    >
      <!-- Expand button when collapsed -->
      <div v-if="isCollapsed" class="expand-button-wrapper" @mousedown.stop>
        <s-btn-icon
          @click="expandDrawer"
          :icon="handleLocation === 'left' ? 'mdi-chevron-right' : 'mdi-chevron-left'"
          density="compact"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useResizeObserver } from '@vueuse/core'

const props = defineProps<{
  minWidth?: number
  maxWidth?: number
  handleLocation: 'left' | 'right'
}>()

const currentWidth = defineModel<number>({ default: 256 })

const COLLAPSE_THRESHOLD = 100
const HANDLE_WIDTH = 8
const CONTENT_MIN_WIDTH = 100

const isDragging = ref(false)
const startX = ref(0)
const startWidth = ref(0)
const tempWidth = ref(0)
const initialWidth = currentWidth.value
const wrapperRef = ref<HTMLElement>()
const parentElement = computed(() => wrapperRef.value?.parentElement)


// Use tempWidth during drag, currentWidth when not dragging
const displayWidth = computed(() => isDragging.value ? tempWidth.value : currentWidth.value)
const isCollapsed = computed(() => displayWidth.value < COLLAPSE_THRESHOLD)

function expandDrawer() {
  currentWidth.value = initialWidth > COLLAPSE_THRESHOLD ? initialWidth : props.minWidth ?? 300
}

/** Extract numeric min-width from CSS styles, returns null if not set or invalid */
function getMinWidthFromStyles(styles: CSSStyleDeclaration): number | null {
  const minWidth = styles.minWidth
  return minWidth && minWidth !== 'auto' && minWidth !== '0px' ? parseFloat(minWidth) : null
}

function calculateSiblingMinWidth(child: HTMLElement): number {
  const styles = window.getComputedStyle(child)
  const isDrawer = child.classList.contains('resizable-drawer-wrapper')
  
  if (isDrawer) {
    const drawerElement = child.querySelector('.resizable-drawer') as HTMLElement
    if (!drawerElement) return HANDLE_WIDTH
    
    const minWidth = getMinWidthFromStyles(window.getComputedStyle(drawerElement))
    return (minWidth ?? drawerElement.getBoundingClientRect().width) + HANDLE_WIDTH
  }
  
  // For non-drawer elements, ensure reasonable minimum space
  const minWidth = getMinWidthFromStyles(styles)
  if (minWidth !== null) return minWidth
  
  const currentWidth = child.getBoundingClientRect().width
  return Math.max(CONTENT_MIN_WIDTH, currentWidth * 0.2)
}

function calculateMaxAvailableWidth(): number {
  if (!parentElement.value) return Infinity

  const parentWidth = parentElement.value.getBoundingClientRect().width
  
  const siblingsMinWidth = Array.from(parentElement.value.children)
    .filter((child): child is HTMLElement => 
      child instanceof HTMLElement && child !== wrapperRef.value
    )
    .reduce((sum, child) => sum + calculateSiblingMinWidth(child), 0)
  
  return parentWidth - siblingsMinWidth - HANDLE_WIDTH
}

function applyWidthConstraints(width: number, maxAvailable: number = Infinity): number {
  const min = props.minWidth ?? 0
  const max = Math.min(
    props.maxWidth ?? Infinity,
    maxAvailable > 0 ? maxAvailable : Infinity
  )
  return Math.max(min, Math.min(max, width))
}

function startResize(event: MouseEvent) {
  isDragging.value = true
  startX.value = event.clientX
  startWidth.value = currentWidth.value
  tempWidth.value = currentWidth.value

  document.body.classList.add('resizable-drawer-resizing')
  document.addEventListener('mousemove', handleResize, { passive: true })
  document.addEventListener('mouseup', stopResize)
  event.preventDefault()
}

function handleResize(event: MouseEvent) {
  if (!isDragging.value) return

  const delta = event.clientX - startX.value
  const rawWidth = props.handleLocation === 'left' 
    ? startWidth.value + delta 
    : startWidth.value - delta

  const maxAvailable = calculateMaxAvailableWidth()
  tempWidth.value = applyWidthConstraints(rawWidth, maxAvailable)
}

function stopResize() {
  isDragging.value = false
  document.body.classList.remove('resizable-drawer-resizing')
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
  currentWidth.value = tempWidth.value
}

function adjustDrawerWidthToFit() {
  if (isDragging.value) return

  const maxAvailable = calculateMaxAvailableWidth()
  if (!isFinite(maxAvailable) || maxAvailable <= 0) return

  const newWidth = applyWidthConstraints(currentWidth.value, maxAvailable)
  if (newWidth !== currentWidth.value) {
    currentWidth.value = newWidth
  }
}

// Observe the parent container for size changes
useResizeObserver(parentElement, () => adjustDrawerWidthToFit());
</script>

<style scoped lang="scss">
.resizable-drawer-wrapper {
  --handle-width: 8px;
  --indicator-width: 3px;
  --indicator-height: 40px;
  --transition-duration: 0.2s;
  
  position: relative;
  height: 100%;
  display: flex;
  flex-shrink: 0;
  z-index: 2;
}

.resizable-drawer {
  position: relative;
  height: 100%;
  background-color: rgb(var(--v-theme-surface));
  overflow: hidden;
  flex-shrink: 0;
  min-width: 0;
}

.resizable-drawer__content {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
}

/* Resize Handle */
.resize-handle {
  position: relative;
  width: var(--handle-width);
  height: 100%;
  cursor: col-resize;
  z-index: 1000;
  flex-shrink: 0;
  background-color: rgb(var(--v-theme-surface));
  border-inline: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  transition: background-color var(--transition-duration) ease;
}

.resize-handle--left {
  order: 2;
}

.resize-handle--right {
  order: -1;
}

.resize-handle:hover {
  background-color: color-mix(in srgb, currentColor 8%, transparent);
}

.resize-handle:is(:active, .resize-handle--active) {
  background-color: color-mix(in srgb, currentColor 12%, transparent);
}

/* Drag indicator */
.resize-handle::before {
  content: '';
  position: absolute;
  inset: 50% auto auto 50%;
  transform: translate(-50%, -50%);
  width: var(--indicator-width);
  height: var(--indicator-height);
  background-color: currentColor;
  border-radius: 2px;
  opacity: 0.15;
  transition: opacity var(--transition-duration) ease;
}

.resize-handle:is(:hover, .resize-handle--active)::before {
  opacity: 0.3;
}

/* Prevent text selection during resize */
.resizing :deep(*) {
  user-select: none !important;
  cursor: col-resize !important;
}

/* Collapsed State */
.collapsed .resizable-drawer {
  width: 0 !important;
  min-width: 0 !important;
}

.collapsed .resizable-drawer__content {
  opacity: 0;
  pointer-events: none;
}

.collapsed .resize-handle {
  background-color: color-mix(in srgb, currentColor 3%, transparent);
}

.collapsed .resize-handle::before {
  display: none;
}

/* Expand Button */
.expand-button-wrapper {
  position: absolute;
  z-index: 10;
  inset: 50% auto auto 50%;
  transform: translate(-50%, -50%);
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 50%;
}

.resize-handle--left .expand-button-wrapper {
  inset-inline-start: 0;
  transform: translate(0, -50%);
  border-inline-start-width: 0;
  border-start-start-radius: 0;
  border-end-start-radius: 0;
}

.resize-handle--right .expand-button-wrapper {
  inset-inline-end: 0;
  inset-inline-start: auto;
  transform: translate(0, -50%);
  border-inline-end-width: 0;
  border-start-end-radius: 0;
  border-end-end-radius: 0;
}
</style>

<style lang="scss">
/* Global styles for resize operation - applied to body */
body.resizable-drawer-resizing,
body.resizable-drawer-resizing * {
  user-select: none !important;
  cursor: col-resize !important;
  pointer-events: none !important;
}

/* Keep the resize handle interactive during drag */
body.resizable-drawer-resizing .resize-handle {
  pointer-events: auto !important;
}
</style>
