<template>
  <v-toolbar 
    density="compact" 
    flat 
    border 
    floating
    rounded
    class="image-editor-toolbar pl-4 pr-4"
  >
    <!-- Shape tools -->
    <markdown-toolbar-button
      @click="setTool(ImageEditorTool.SELECT)"
      title="Select and Move [V]"
      icon="mdi-cursor-default"
      :active="activeTool === ImageEditorTool.SELECT"
    />
    <span class="separator" />
    
    <markdown-toolbar-button
      @click="setTool(ImageEditorTool.RECTANGLE_OUTLINED)"
      title="Rectangle (Outline) [R]"
      icon="mdi-rectangle-outline"
      :active="activeTool === ImageEditorTool.RECTANGLE_OUTLINED"
    />
    <markdown-toolbar-button
      @click="setTool(ImageEditorTool.RECTANGLE_FILLED)"
      title="Rectangle (Filled) [Shift+R]"
      icon="mdi-rectangle"
      :active="activeTool === ImageEditorTool.RECTANGLE_FILLED"
    />
    <markdown-toolbar-button
      @click="setTool(ImageEditorTool.PIXELATE)"
      title="Pixelate [P]"
      icon="mdi-blur"
      :active="activeTool === ImageEditorTool.PIXELATE"
    />
    <markdown-toolbar-button
      @click="setTool(ImageEditorTool.ELLIPSE)"
      title="Ellipse (Outline) [O]"
      icon="mdi-ellipse-outline"
      :active="activeTool === ImageEditorTool.ELLIPSE"
    />
    <markdown-toolbar-button
      @click="setTool(ImageEditorTool.LINE)"
      title="Line [L]"
      icon="mdi-vector-line"
      :active="activeTool === ImageEditorTool.LINE"
    />
    <markdown-toolbar-button
      @click="setTool(ImageEditorTool.TEXT)"
      title="Text [T]"
      icon="mdi-format-text"
      :active="activeTool === ImageEditorTool.TEXT"
    />
    <markdown-toolbar-button
      @click="setTool(ImageEditorTool.MARKER)"
      title="Numbered Marker [M]"
      icon="mdi-numeric-1-circle"
      :active="activeTool === ImageEditorTool.MARKER"
    />
    <s-tooltip v-if="activeTool === ImageEditorTool.MARKER" text="Marker number (auto-increments after placing)" location="top">
      <template #activator="{ props: tooltipProps }">
        <s-number-input
          v-model="markerNumber"
          :min="1"
          v-bind="tooltipProps"
          density="compact"
          class="marker-number-input"
        />
      </template>
    </s-tooltip>
    
    <span class="separator" />
    
    <markdown-toolbar-button
      @click="setTool(ImageEditorTool.CROP)"
      title="Crop"
      icon="mdi-crop"
      :active="activeTool === ImageEditorTool.CROP"
    />
    <template v-if="activeTool === ImageEditorTool.CROP">
      <markdown-toolbar-button
        @click="setTool(ImageEditorTool.SELECT)"
        title="Apply Crop"
        icon="mdi-check"
        color="success"
      />
      <markdown-toolbar-button
        @click="emit('cancelCrop')"
        title="Cancel Crop"
        icon="mdi-close"
        color="error"
      />
    </template>
    
    <span class="separator" />
    
    <!-- Color picker -->
    <s-color-picker 
      v-model="localSettings.imageEditorSettings.color" 
      :show-swatches="true"
      :swatches="colorSwatches"
    >
      <template #activator="{ props: colorPickerProps }">
        <s-btn-icon
          v-bind="colorPickerProps"
          size="small"
          density="comfortable"
        >
          <v-badge
            :color="localSettings.imageEditorSettings.color"
            dot
            :offset-x="-2"
            :offset-y="-2"
          >
            <v-icon size="small" icon="mdi-palette" />
          </v-badge>
          <s-tooltip activator="parent" location="top" text="Color" />
        </s-btn-icon>
      </template>
    </s-color-picker>
    
    <s-tooltip text="Stroke width" location="top">
      <template #activator="{ props: tooltipProps }">
        <s-number-input
          v-model="localSettings.imageEditorSettings.strokeWidth"
          :min="1"
          @wheel="onWheel"
          v-bind="tooltipProps"
        >
          <template #prepend>
            <v-icon size="small" icon="mdi-format-vertical-align-center" />
          </template>
        </s-number-input>
      </template>
    </s-tooltip>
  </v-toolbar>
</template>

<script setup lang="ts">
import { ImageEditorTool } from './ImageEditor.vue';

const activeTool = defineModel<ImageEditorTool>('activeTool', { required: true });
const markerNumber = defineModel<number>('markerNumber', { required: true });

const emit = defineEmits<{
  cancelCrop: [];
}>();

const localSettings = useLocalSettings();

const colorSwatches = [
  ['#FF0000'], ['#FF6B00'], ['#FFD700'], ['#008000'], ['#00FF00'],
  ['#000000'], ['#808080'], ['#FFFFFF'], ['#0000FF'], ['#00FFFF'], 
];

function setTool(tool: ImageEditorTool) {
  activeTool.value = tool;
}

const strokeWheelAccum = ref(0);
const WHEEL_DELTA_PER_INCREMENT = 100;
function onWheel(event: WheelEvent) {
  if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) {
    return;
  }

  event.preventDefault();
  event.stopPropagation();

  strokeWheelAccum.value += event.deltaY;
  const min = 1;

  while (strokeWheelAccum.value >= WHEEL_DELTA_PER_INCREMENT) {
    strokeWheelAccum.value -= WHEEL_DELTA_PER_INCREMENT;
    localSettings.imageEditorSettings.strokeWidth = Math.max(min, localSettings.imageEditorSettings.strokeWidth - 1);
  }
  while (strokeWheelAccum.value <= -WHEEL_DELTA_PER_INCREMENT) {
    strokeWheelAccum.value += WHEEL_DELTA_PER_INCREMENT;
    localSettings.imageEditorSettings.strokeWidth = Math.max(min, localSettings.imageEditorSettings.strokeWidth + 1);
  }
}

// Keyboard shortcuts for tool selection
useHotkey('v', () => setTool(ImageEditorTool.SELECT));
useHotkey('r', () => setTool(ImageEditorTool.RECTANGLE_OUTLINED));
useHotkey('shift+r', () => setTool(ImageEditorTool.RECTANGLE_FILLED));
useHotkey('p', () => setTool(ImageEditorTool.PIXELATE));
useHotkey('o', () => setTool(ImageEditorTool.ELLIPSE));
useHotkey('l', () => setTool(ImageEditorTool.LINE));
useHotkey('t', () => setTool(ImageEditorTool.TEXT));
useHotkey('m', () => setTool(ImageEditorTool.MARKER));
</script>

<style scoped lang="scss">
.image-editor-toolbar {
  position: absolute;
  top: 2px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1;
}

.separator {
  display: inline-block;
  height: 1.5em;
  width: 0;
  border-left: 1px solid #d9d9d9;
  border-right: 1px solid #fff;
  color: transparent;
  text-indent: -10px;
  margin: 0 0.5em;
}

.v-number-input:deep() {
  max-width: 4.5em;
  margin-left: 0.5em;
  --v-input-control-height: 24px !important;
  --v-input-padding-top: 3px !important;
  --v-input-padding-bottom: 3px !important;

  .v-field input {
    --v-field-input-padding-bottom: 0;
    --v-field-padding-start: 0;
    --v-field-padding-end: 0;
    text-align: center;
    font-size: 0.9em;
  }
  .v-field__append-inner {
    .v-btn--icon {
      width: 1.5em !important;
    }
    .v-icon {
      --v-icon-size-multiplier: 0.8;
    }
  }
  .v-input__prepend {
    margin-inline-end: 0.25em;
    .v-icon {
      opacity: 1;
    }
  }
}

.marker-number-input:deep() {
  max-width: 3.5em;
  margin-left: 0.5em;
  transition: opacity 0.2s;

  &:hover, &:focus-within {
    opacity: 1;
  }

  .v-field input {
    font-size: 0.85em;
  }
}
</style>
