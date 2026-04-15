<template>
  <div class="image-editor ">
    <!-- Toolbar -->
    <markdown-image-editor-toolbar
      v-model:active-tool="activeTool"
      v-model:marker-number="markerCounter"
      @cancel-crop="onCancelCrop"
    />
    
    <!-- Canvas -->
    <div 
      ref="containerEl"
      class="image-editor-container"
    >
      <div class="canvas-wrapper elevation-4">
        <canvas ref="canvasEl" />
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { 
  Canvas, Rect, Ellipse, Polyline, Polygon, FabricImage, type FabricObject, Point, IText, Group, Circle, Control,
  type TPointerEvent, type Transform, util as fabricUtil, controlsUtils,
} from 'fabric';
import { useZoomImage } from '@base/utils/helpers';

export enum ImageEditorTool {
  SELECT = 'select',
  RECTANGLE_OUTLINED = 'rectangle_outlined',
  RECTANGLE_FILLED = 'rectangle_filled',
  PIXELATE = 'pixelate',
  ELLIPSE = 'ellipse',
  LINE = 'line',
  TEXT = 'text',
  MARKER = 'marker',
  CROP = 'crop',
}
</script>

<script setup lang="ts">
const props = defineProps<{
  imageSrc: string;
}>();

const activeTool = ref<ImageEditorTool>(ImageEditorTool.SELECT);
const hasChanges = ref(false);
const localSettings = useLocalSettings();

const canvasEl = useTemplateRef('canvasEl');
const containerEl = useTemplateRef('containerEl');
const canvas = shallowRef<Canvas | null>(null);

const selectModeArgs = computed(() => {
  const isSelectMode = activeTool.value === ImageEditorTool.SELECT;
  return {
    selectable: isSelectMode,
    evented: isSelectMode,
    hasControls: isSelectMode,
    hasBorders: isSelectMode,
    lockMovementX: !isSelectMode,
    lockMovementY: !isSelectMode,
  };
});
const fontSize = computed(() => localSettings.imageEditorSettings.strokeWidth * 12);

// Drawing state
const isDrawing = ref(false);
const drawingShape = shallowRef<FabricObject|null>(null);
const drawStartX = ref(0);
const markerCounter = ref(1);
const drawStartY = ref(0);

// Crop mode
const cropRect = shallowRef<FabricObject|null> (null);
const cropBackground = shallowRef<FabricObject|null>(null);
const cropExcludeObjects = computed(() => new Set([cropRect.value, cropBackground.value].filter(Boolean) as FabricObject[]));
const pixelationSource = usePixelationSource(canvas, {
  excludeObjects: cropExcludeObjects,
});


// Initialize canvas
onMounted(async () => {
  if (!canvasEl.value) {
    return;
  }
  const img = await FabricImage.fromURL(props.imageSrc, {});
  img.positionByLeftTop(new Point(0, 0));

  canvas.value = new Canvas(canvasEl.value, {
    width: img.width,
    height: img.height,
    backgroundImage: img,
  });
  updateSize();

  // Event handlers
  setupDrawingHandlers();
  setupChangeTracking();

  canvas.value.renderAll();
  return canvas.value;
});
onBeforeUnmount(() => {
  if (canvas.value) {
    canvas.value.dispose();
    canvas.value = null;
  }
});

const { scaleFactor } = useZoomImage(containerEl, () => (canvas.value ? { width: canvas.value.width, height: canvas.value.height } : null));
function resizeControls() {
  const scale = scaleFactor.value;
  const cornerSize = Math.max(10 / scale, 6);
  canvas.value?.forEachObject((obj) => {
    obj.set({
      cornerSize,
      borderWidth: 2 / scale,
      transparentCorners: false,
    });
  });

  if (cropRect.value) {
    const cropRectCornerSize = 20;
    cropRect.value.set({
      cornerSize: cropRectCornerSize,
      borderWidth: 2,
      transparentCorners: false,
    })
    cropRect.value.forEachControl((c) => {
      c.sizeX = cropRectCornerSize;
      c.sizeY = cropRectCornerSize;
      c.offsetX = (cropRectCornerSize * -0.5) * Math.sign(c.x);
      c.offsetY = (cropRectCornerSize * -0.5) * Math.sign(c.y);
    });
    cropRect.value.setCoords();
  }
}
function updateSize() {
  if (!canvas.value) { 
    return;
  }
  const scale = scaleFactor.value;
  canvas.value.setDimensions({
    width: canvas.value.width * scale,
    height: canvas.value.height * scale,
  }, {
    cssOnly: true,
  });
  resizeControls();
  canvas.value.requestRenderAll();
}
watch(scaleFactor, () => updateSize());

watch(activeTool, (tool, oldTool) =>  {
  if (!canvas.value) { 
    return;
  }

  if (tool === ImageEditorTool.CROP) {
    enterCropMode();
  } else if (oldTool === ImageEditorTool.CROP) {
    exitCropMode({ apply: true });
  }
  
  canvas.value.selection = (tool === ImageEditorTool.SELECT);
  
  // Discard active selection when not in SELECT mode
  if ([ImageEditorTool.SELECT, ImageEditorTool.CROP].includes(tool)) {
    resizeControls();
  } else {
    canvas.value.discardActiveObject();
  }
  
  canvas.value.forEachObject((obj) => {
    if (cropExcludeObjects.value.has(obj)) {
      return;
    }
        obj.set(selectModeArgs.value);
    obj.setCoords();
  });
  canvas.value.requestRenderAll();
});

function setupChangeTracking() {
  if (!canvas.value) {
    return;
  }

  function onChange(e: any) {
    if (e.target && !cropExcludeObjects.value.has(e.target)) {
      hasChanges.value = true;
    }
  }

  canvas.value.on('object:added', onChange);
  canvas.value.on('object:modified', onChange);
  canvas.value.on('object:removed', onChange);
  canvas.value.on('text:changed', onChange);
}

function setupDrawingHandlers() {
  if (!canvas.value) { 
    return;
  }
  
  canvas.value.on('mouse:down', (event) => {
    if (!canvas.value || [ImageEditorTool.SELECT, ImageEditorTool.CROP].includes(activeTool.value)) {
      return;
    } else if (activeTool.value === ImageEditorTool.TEXT) {
      // Text tool: add on click
      const pointer = canvas.value!.getScenePoint(event.e);
      addTextAtPosition(pointer.x, pointer.y);
      return;
    } else {
      // Begin drawing shape at position
      isDrawing.value = true;
      const pointer = canvas.value!.getScenePoint(event.e);
      drawStartX.value = pointer.x;
      drawStartY.value = pointer.y;
      
      const shape = createDrawingShape(pointer.x, pointer.y);
      if (shape) {
        canvas.value.add(shape);
        drawingShape.value = shape;
      }
    }
  });
  
  canvas.value.on('mouse:move', (event) => {
    if (!isDrawing.value || !drawingShape.value) { 
      return;
    }
    
    const pointer = canvas.value!.getScenePoint(event.e);
    updateDrawingShape(pointer.x, pointer.y);
    canvas.value!.renderAll();
  });
  
  canvas.value.on('mouse:up', () => {
    if (!canvas.value || !isDrawing.value || !drawingShape.value) {
      return;
    }
    isDrawing.value = false;
    const shape = drawingShape.value;
    drawingShape.value = null;
  
    // Make the shape selectable only if in SELECT mode
    shape.set(selectModeArgs.value);
    shape.setCoords();
    
    // Increment marker counter if a marker was just created
    if (activeTool.value === ImageEditorTool.MARKER) {
      markerCounter.value++;
    }
    
    // Don't select the shape automatically - let user decide
    canvas.value.discardActiveObject();
    canvas.value.requestRenderAll();
  });
}

function createDrawingShape(x: number, y: number) {
  switch (activeTool.value) {
    case ImageEditorTool.RECTANGLE_OUTLINED: {
      return new Rect({
        left: x,
        top: y,
        width: 0,
        height: 0,
        fill: 'transparent',
        stroke: localSettings.imageEditorSettings.color,
        strokeWidth: localSettings.imageEditorSettings.strokeWidth,
      });
    }
    case ImageEditorTool.RECTANGLE_FILLED: {
      return new Rect({
        left: x,
        top: y,
        width: 0,
        height: 0,
        fill: localSettings.imageEditorSettings.color,
        stroke: localSettings.imageEditorSettings.color,
        strokeWidth: 0,
      });
    }
    case ImageEditorTool.PIXELATE: {
      return new PixelateRect({
        left: x,
        top: y,
        width: 0,
        height: 0,
        originX: 'left',
        originY: 'top',
        pixelationSource,
      });
    }
    case ImageEditorTool.ELLIPSE: {
      return new Ellipse({
        left: x,
        top: y,
        rx: 0,
        ry: 0,
        fill: 'transparent',
        stroke: localSettings.imageEditorSettings.color,
        strokeWidth: localSettings.imageEditorSettings.strokeWidth,
        originX: 'center',
        originY: 'center',
      });
    } 
    case ImageEditorTool.LINE: {
      return new Polyline([{ x: 0, y: 0 }, { x: 0, y: 0 }], {
        left: x,
        top: y,
        originX: 'center',
        originY: 'center',
        stroke: localSettings.imageEditorSettings.color,
        strokeWidth: localSettings.imageEditorSettings.strokeWidth,
        fill: 'transparent',
        objectCaching: false,
      });
    }
    case ImageEditorTool.MARKER: {
      const circle = new Circle({
        radius: fontSize.value * 0.8,
        fill: localSettings.imageEditorSettings.color,
        strokeWidth: 0,
        originX: 'center',
        originY: 'center',
      });
      
      const text = new IText(markerCounter.value.toString(), {
        fontSize: fontSize.value,
        fill: getContrastTextColor(localSettings.imageEditorSettings.color),
        originX: 'center',
        originY: 'center',
        fontFamily: 'Noto Sans',
        fontWeight: 'bold',
      });
      
      const pointer = new Polygon([{ x: 0, y: 0 }, { x: 0, y: 0 }, { x: 0, y: 0 }], {
        fill: localSettings.imageEditorSettings.color,
        stroke: localSettings.imageEditorSettings.color,
        strokeWidth: 0,
        originX: 'left',
        originY: 'center',
        objectCaching: false,
      });
      
      const group = new Group([circle, pointer, text], {
        left: x,
        top: y,
        originX: 'center',
        originY: 'center',
        subTargetCheck: false,
        objectCaching: false,
        lockScalingFlip: true,
      });
      
      const pointerTipControl = new Control({
        x: 0,
        y: 0,
        cursorStyle: 'move',
        actionHandler: (eventData: TPointerEvent, transform: Transform) => {
          const group = transform.target as Group;
          const canvas = group.canvas;
          if (!canvas) { 
            return false;
          }
          const pointerPos = canvas.getScenePoint(eventData);
          updateMarkerShape(group, pointerPos.x, pointerPos.y);
          return true;
        },
        positionHandler: (_dim, _finalMatrix, fabricObject) => {
          const group = fabricObject as Group;
          const pointer = group.item(1) as Polygon;
          const tip = pointer.points[1]!;
          return new Point(tip.x - pointer.pathOffset.x, tip.y - pointer.pathOffset.y)
            .transform(fabricUtil.multiplyTransformMatrices(pointer.getViewportTransform(), pointer.calcTransformMatrix()))
        },
        render: (ctx, left, top, styleOverride, fabricObject) => {
          styleOverride = {
            ...styleOverride,
            cornerStyle: 'circle',
          }
          return controlsUtils.renderCircleControl.call(pointerTipControl, ctx, left, top, styleOverride, fabricObject);
        },
      });
      group.controls.tip = pointerTipControl;

      return group;
    }
  }

  return null;
}

function updateDrawingShape(x: number, y: number) {
  if (!drawingShape.value) { 
    return;
  }
  
  const tool = activeTool.value;
  const startX = drawStartX.value;
  const startY = drawStartY.value;
  const width = Math.abs(x - startX);
  const height = Math.abs(y - startY);
  
  switch (tool) {
    case ImageEditorTool.RECTANGLE_OUTLINED:
    case ImageEditorTool.RECTANGLE_FILLED:
    case ImageEditorTool.PIXELATE: {
      // Calculate top-left corner position regardless of drag direction
      const left = Math.min(startX, x);
      const top = Math.min(startY, y);
      drawingShape.value.set({
        left,
        top,
        width,
        height,
        originX: 'left',
        originY: 'top',
      });
      break;
    } 
    case ImageEditorTool.ELLIPSE: {
      // Position ellipse so clicked point is on edge, not center
      const centerX = (startX + x) / 2;
      const centerY = (startY + y) / 2;
      const rx = width / 2;
      const ry = height / 2;
      drawingShape.value.set({
        left: centerX,
        top: centerY,
        rx,
        ry,
      });
      break;
    }
    case ImageEditorTool.LINE: {
      // Center the line between start and end points
      const line = drawingShape.value as Polyline;
      const centerX = (startX + x) / 2;
      const centerY = (startY + y) / 2;
      const halfDx = (x - startX) / 2;
      const halfDy = (y - startY) / 2;
      
      line.set({
        left: centerX,
        top: centerY,
        points: [
          { x: -halfDx, y: -halfDy },
          { x: halfDx, y: halfDy }
        ],
      });
      line.setBoundingBox();
      line.setCoords();
      break;
    }
    case ImageEditorTool.MARKER: {
      updateMarkerShape(drawingShape.value, x, y);
      break;
    }
  }
}

function updateMarkerShape(shape: FabricObject, x: number, y: number) {
  const group = shape as Group;
  if (!group || group.type !== 'group' || group.size() < 3 || group.item(0).type !== 'circle' || group.item(1).type !== 'polygon') {
    return;
  }
  const pointer = group.item(1) as Polygon;
  const circle = group.item(0) as Circle;
  
  // Convert mouse position from canvas coordinates to group's local coordinates
  // to properly handle group transformations (scaling, rotation)
  const mousePoint = new Point(x, y)
    .transform(fabricUtil.invertTransform(group.calcTransformMatrix()));
  
  const distance = Math.sqrt(Math.pow(mousePoint.x, 2) + Math.pow(mousePoint.y, 2));
  const angle = Math.atan2(mousePoint.y, mousePoint.x) * 180 / Math.PI;
  const baseWidth = circle.radius * 0.5;
  pointer.set({
    left: 0,
    top: 0,
    angle,
    points: [
      { x: 0, y: -baseWidth },
      { x: distance, y: 0 },
      { x: 0, y: baseWidth },
    ],
  });
  pointer.setBoundingBox();
  
  group.setCoords();
}

function addTextAtPosition(x: number, y: number) {
  if (!canvas.value) { 
    return;
  }
  
  const text = new IText('Text', {
    left: x,
    top: y,
    fontSize: fontSize.value,
    fill: localSettings.imageEditorSettings.color,
    fontFamily: 'Noto Sans',
    ...selectModeArgs.value,
  });
  canvas.value.add(text);
  
  // Only enter editing mode and select if in TEXT mode (for immediate editing)
  if (activeTool.value === ImageEditorTool.TEXT) {
    canvas.value.setActiveObject(text);
    text.enterEditing();
    text.selectAll();
  }
  
  canvas.value.requestRenderAll();
}

function getContrastTextColor(bgColor: string): string {
  // Remove # if present
  const hex = bgColor.replace('#', '');
  
  // Convert to RGB
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  
  // Calculate relative luminance (perceived brightness)
  // Using the formula: (0.299*R + 0.587*G + 0.114*B)
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b);
  
  // Return white for dark backgrounds, black for light backgrounds
  return luminance > 128 ? '#000000' : '#ffffff';
}

function deleteSelected() {
  if (!canvas.value) { 
    return;
  }
  
  const activeObjects = canvas.value.getActiveObjects()
    .filter(o => !cropExcludeObjects.value.has(o));
  if (activeObjects.length > 0) {
    canvas.value.remove(...activeObjects);
    canvas.value.discardActiveObject();
    canvas.value.renderAll();
  }
}
useHotkey('Delete', deleteSelected);
useHotkey('Backspace', deleteSelected);


function enterCropMode() {
  if (!canvas.value) { 
    return;
  }

  // Create crop rectangle spanning entire image
  cropRect.value = new Rect({
    left: 0,
    top: 0,
    width: canvas.value.width,
    height: canvas.value.height,
    originX: 'left',
    originY: 'top',
    fill: 'transparent',
    minScaleLimit: 0.1,
    lockScalingFlip: true,
  });
  cropRect.value.setControlsVisibility({ mtr: false }); // Hide rotation control

  cropBackground.value = new Rect({
    left: canvas.value.width / 2,
    top: canvas.value.height / 2,
    width: canvas.value.width * 3,
    height: canvas.value.height * 3,
    fill: 'rgba(0,0,0,0.5)',
    selectable: false,
    evented: false,
    hasControls: false,
    clipPath: new Group([new Rect({
      left: 0,
      top: 0,
      width: canvas.value.width,
      height: canvas.value.height,
      originX: 'left',
      originY: 'top',
    })], {
      inverted: true,
      absolutePositioned: true,
    }),
  });

  cropRect.value.on('deselected', () => {
    if (cropRect.value) {
      canvas.value?.setActiveObject(cropRect.value!);
    }
  });
  cropRect.value.on('moving', (e) => {
    const obj = cropRect.value;
    if (!obj || !canvas.value) {
      return;
    }

    const oldRect = obj.getBoundingRect();
    const newPos = new Point(
      Math.min(canvas.value.width - oldRect.width, Math.max(0, obj.left!)),
      Math.min(canvas.value.height - oldRect.height, Math.max(0, obj.top!))
    );
    obj.setPositionByOrigin(newPos, 'left', 'top');
    if (cropBackground.value) {
      cropBackground.value.clipPath = new Group([new Rect({
        left: newPos.x,
        top: newPos.y,
        width: oldRect.width,
        height: oldRect.height,
        originX: 'left',
        originY: 'top',
      })], {
        inverted: true,
        absolutePositioned: true,
      });
    }
  });
  cropRect.value.on('scaling', () => {
    const obj = cropRect.value;
    if (!obj || !canvas.value) {
      return;
    }

    obj.setCoords();
    const rect = obj.getBoundingRect();

    const update: any = {};
    if (rect.left < 0) {
      update.left = rect.left = 0;
      update.scaleX = 1;
    }
    if (rect.top < 0) {
      update.top = rect.top = 0;
      update.scaleY = 1;
    }
    if (rect.left + rect.width > canvas.value.width) {
      update.width = rect.width = canvas.value.width - rect.left;
      update.scaleX = 1;
    }
    if (rect.top + rect.height > canvas.value.height) {
      update.height = rect.height = canvas.value.height - rect.top;
      update.scaleY = 1;
    }
    if (update) {
      obj.set(update);
      obj.setCoords();
    }
    
    if (cropBackground.value) {
      cropBackground.value.clipPath = new Group([new Rect({
        ...obj.getBoundingRect(),
        originX: 'left',
        originY: 'top',
      })], {
        inverted: true,
        absolutePositioned: true,
      });
    }
  })

  canvas.value.add(cropBackground.value);
  canvas.value.add(cropRect.value);
  canvas.value.setActiveObject(cropRect.value);
  resizeControls();
  canvas.value.renderAll();
}

function exitCropMode(options?: { apply?: boolean }) {
  if (!canvas.value || !cropRect.value || !canvas.value.contains(cropRect.value)) {
    return;
  }

  const cropRectObj = cropRect.value;
  const area = cropRectObj.getBoundingRect();

  canvas.value.remove(cropBackground.value!);
  cropBackground.value = null;
  cropRect.value = null;
  canvas.value.remove(cropRectObj);
  canvas.value.renderAll();
  
  // Check if actual cropping happened (dimensions changed)
  const isCropped = area.left !== 0 || area.top !== 0 || 
                    area.width !== canvas.value.width || area.height !== canvas.value.height;
  if (!isCropped || !options?.apply) {
    return;
  }

  function updatePosAfterCrop(obj?: FabricObject) {
    if (!obj) {
      return;
    }
    const pos = obj.getBoundingRect();
    obj.setPositionByOrigin(new Point(pos.left - area.left, pos.top - area.top), 'left', 'top');
    obj.setCoords();
  }
  
  updatePosAfterCrop(canvas.value.backgroundImage);
  canvas.value.getObjects().forEach(updatePosAfterCrop);
  canvas.value.setDimensions({ width: area.width, height: area.height }, { backstoreOnly: true });
  updateSize();
  
  hasChanges.value = true;
}

function onCancelCrop() {
  exitCropMode({ apply: false });
  activeTool.value = ImageEditorTool.SELECT;
}

// Set colors
function updateActiveObjects(values: Record<string, any>, predicate?: (obj: FabricObject) => boolean) {
  if (!canvas.value) {
    return;
  }
  
  let activeObjects = canvas.value.getActiveObjects();
  if (predicate) {
    activeObjects = activeObjects.filter(predicate);
  }
  activeObjects.forEach((obj) => {
    obj.set(values);
  });
  canvas.value.renderAll();
}
watch(() => localSettings.imageEditorSettings.color, (color) => {
  updateActiveObjects({ stroke: color }, (obj) => !!obj.stroke && obj.stroke !== 'transparent');
  updateActiveObjects({ fill: color }, (obj) => obj.fill !== 'transparent');
});
watch(() => localSettings.imageEditorSettings.strokeWidth, (width) => {
  updateActiveObjects({ strokeWidth: width }, (obj) => obj.strokeWidth > 0);
  updateActiveObjects({ fontSize: fontSize.value }, (obj) => obj.type === 'i-text' || obj.type === 'text');
});

async function exportAsBlob(): Promise<Blob | null> {
  if (!canvas.value) {
    return null;
  }
  if (activeTool.value === ImageEditorTool.CROP) {
    exitCropMode({ apply: true });
  }

  return await canvas.value.toBlob({
    multiplier: 1,
    format: 'png',
    quality: 0.95,
  }) || null;
}

defineExpose({
  exportAsBlob,
  hasChanges: computed(() => hasChanges.value || (activeTool.value === ImageEditorTool.CROP)),
});
</script>

<style scoped lang="scss">
.image-editor {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

.image-editor-container {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  flex: 1;
  overflow: auto;
  padding: 0.5rem;
  padding-top: 3.5rem;
  position: relative;
  touch-action: none;
}
.canvas-wrapper {
  background: 
    repeating-conic-gradient(rgb(var(--v-theme-surface)) 0% 25%, rgba(var(--v-theme-on-surface), 0.1) 0% 50%) 
    50% / 20px 20px;
}

</style>

