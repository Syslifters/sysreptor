<template>
  <iframe ref="pdfviewer" src="/static/pdfviewer/viewer.html" @load="iframeLoaded = true" class="pdfviewer" :class="{loading: !iframeLoaded}" title="PDF Viewer" />
</template>

<script>
export default {
  props: {
    value: {
      type: Uint8Array,
      default: null,
    },
  },
  data() {
    return {
      iframeLoaded: false,
    };
  },
  watch: {
    value() {
      this.updatePdf();
    },
    iframeLoaded() {
      this.updatePdf();
    },
  },
  methods: {
    updatePdf() {
      if (!this.$refs.pdfviewer || !this.iframeLoaded || !this.value) {
        return;
      }
      const msg = new Uint8Array(this.value);
      this.$refs.pdfviewer.contentWindow.postMessage(msg, window.origin, [msg.buffer]);
    },
  },
}
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
