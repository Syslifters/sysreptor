<template>
  <div ref="container" class="pdf-container">
    <div ref="viewer" class="pdfViewer" />
  </div>
</template>

<script>
// TODO: allow zooming: Ctrl + MouseWheel?

import { getDocument } from 'pdfjs-dist/webpack';
import { EventBus } from 'pdfjs-dist/lib/web/event_utils';
import { LinkTarget, PDFLinkService } from 'pdfjs-dist/lib/web/pdf_link_service';
import { PDFFindController } from 'pdfjs-dist/lib/web/pdf_find_controller';
import { PDFScriptingManager } from 'pdfjs-dist/lib/web/pdf_scripting_manager';
import { PDFViewer } from 'pdfjs-dist/lib/web/pdf_viewer';

export default {
  props: {
    value: {
      type: Uint8Array,
      required: true,
    },
  },
  data() {
    return {
      eventBus: null,
      linkService: null,
      findController: null,
      scriptingManager: null,
      pdfViewer: null,

      resizeObserver: null,
    }
  },
  watch: {
    value: {
      immediate: true,
      handler () {
        this.renderPdf();
      }
    }
  },
  mounted() {
    this.eventBus = new EventBus();
    this.linkService = new PDFLinkService({ eventBus: this.eventBus, externalLinkTarget: LinkTarget.BLANK });
    this.findController = new PDFFindController({ linkService: this.linkService, eventBus: this.eventBus });
    this.scriptingManager = new PDFScriptingManager({ eventBus: this.eventBus });
    this.pdfViewer = new PDFViewer({
      container: this.$refs.container,
      viewer: this.$refs.viewer,
      eventBus: this.eventBus,
      linkService: this.linkService,
      findController: this.findController,
    });
    this.linkService.setViewer(this.pdfViewer);

    this.resizeObserver = new ResizeObserver(this.onResize);
    this.resizeObserver.observe(this.$refs.container);
  },
  beforeDestroy() {
    this.resizeObserver.unobserve(this.$refs.container);
  },
  methods: {
    async renderPdf() {
      // Restore scroll position
      if (this.$refs.container && this.eventBus) {
        const scroll = this.$refs.container.scrollTop || 0;
        this.eventBus.on('pagerendered', () => { this.$refs.container.scrollTop = scroll; }, { once: true });
      }

      // Load new PDF
      const doc = await getDocument(this.value).promise;
      this.pdfViewer.setDocument(doc);
      this.linkService.setDocument(doc, null);
      this.findController.setDocument(doc);
      this.onResize();
    },
    onResize() {
      this.pdfViewer.currentScaleValue = 'page-width';
    },
  }
}
</script>

<style lang="scss">
@import 'pdfjs-dist/web/pdf_viewer.css';

:root {
  --page-border: 0;
  --page-margin: 1em;
}

.pdf-container {
  position: absolute;
  background: #585858;
  height: 100%;
  width: 100%;
  overflow: auto;
}
</style>
