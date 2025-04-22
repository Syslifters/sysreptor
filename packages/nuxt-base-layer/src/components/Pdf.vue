<template>
  <iframe
    ref="iframeRef"
    src="/static/pdfviewer/dist/viewer.html"
    @load="iframeLoaded = true"
    class="pdfviewer"
    :class="{loading: !iframeLoaded}"
    :style="{ 
      colorScheme: theme.current.value.dark ? 'dark': 'light',
    }"
    title="PDF Viewer"
  />
</template>

<script setup lang="ts">
import { decode as base64decode } from 'base64-arraybuffer';

const props = defineProps<{
  value: Uint8Array|string|null;
}>();

const theme = useTheme();

const iframeRef = ref();
const iframeLoaded = ref(false);
async function updatePdf() {
  if (!iframeRef.value || !iframeLoaded.value || !props.value) {
    return;
  }
  let msg = null;
  if (typeof props.value === 'string') {
    msg = new Uint8Array(base64decode(props.value));
  } else {
    msg = new Uint8Array(props.value);
  }
  iframeRef.value.contentWindow.postMessage(msg, window.origin, [msg.buffer]);
}
watch([() => props.value, iframeLoaded], () => updatePdf())
</script>

<style lang="scss" scoped>
  .pdfviewer {
    display: block;
    width: 100%;
    height: 100%;
    border: 0;
    user-select: none;
  }
  .loading {
    height: 0;
  }
</style>
