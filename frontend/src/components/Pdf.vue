<template>
  <iframe
    ref="iframeRef"
    src="/static/pdfviewer/viewer.html"
    @load="iframeLoaded = true"
    class="pdfviewer"
    :class="{loading: !iframeLoaded}"
    title="PDF Viewer"
  />
</template>

<script setup lang="ts">
const props = defineProps<{
  value: Uint8Array|string|null;
}>();

const iframeRef = ref();
const iframeLoaded = ref(false);
async function updatePdf() {
  if (!iframeRef.value || !iframeLoaded.value || !props.value) {
    return;
  }
  let msg = null;
  if (typeof props.value === 'string') {
    msg = new Uint8Array(await (await fetch("data:application/pdf;base64," + props.value)).arrayBuffer());
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
  }
  .loading {
    height: 0;
  }
</style>
