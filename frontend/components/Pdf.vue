<template>
  <iframe ref="pdfviewer" src="/static/pdfviewer/viewer.html" @load="iframeLoaded = true" class="pdfviewer" :class="{loading: !iframeLoaded}" title="PDF Viewer" />
</template>

<script>
export default {
  props: {
    value: {
      type: [Uint8Array, String],
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
    async updatePdf() {
      if (!this.$refs.pdfviewer || !this.iframeLoaded || !this.value) {
        return;
      }
      let msg = null;
      if (typeof this.value === 'string') {
        msg = new Uint8Array(await (await fetch("data:application/pdf;base64," + this.value)).arrayBuffer());
      } else {
        msg = new Uint8Array(this.value);
      }
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
