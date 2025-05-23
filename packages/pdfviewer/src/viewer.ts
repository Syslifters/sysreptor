import { 
  GlobalWorkerOptions,
  InvalidPDFException,
  PDFDocumentLoadingTask,
  PDFDocumentProxy,
  getDocument,
  version as pdfjsVersion,
  build as pdfjsBuild,
  TouchManager,
} from 'pdfjs-dist';
import {
  PDFViewer,
  PDFLinkService,
  EventBus,
  LinkTarget,
  GenericL10n,
  DownloadManager,
  PDFFindController,
  FindState,
} from 'pdfjs-dist/web/pdf_viewer.mjs';

// Set up the PDF.js worker
GlobalWorkerOptions.workerPort = new Worker(new URL('pdfjs-dist/build/pdf.worker.mjs', import.meta.url), { type: 'module' });

const DEFAULT_SCALE_VALUE = 'auto';

type PDFViewerApplicationConfig = {
  appContainer: HTMLElement;
  mainContainer: HTMLDivElement;
  viewerContainer: HTMLDivElement;
  toolbar: {
    zoomIn: HTMLButtonElement;
    zoomOut: HTMLButtonElement;
    scaleSelect: HTMLSelectElement;
    customScaleOption: HTMLOptionElement;
    
    pageNumber: HTMLInputElement;
    numPages: HTMLElement;

    download: HTMLButtonElement;
  },
  findBar: {
    findbar: HTMLElement;
    findInput: HTMLInputElement;
    findResultsCount: HTMLElement;
    findMsg: HTMLElement;
    findPrevious: HTMLButtonElement;
    findNext: HTMLButtonElement;
    findClose: HTMLButtonElement;
  }
}

type FindUpdateEvent = {
  state: number;
  previous: boolean;
  matchesCount: {
    current: number;
    total: number;
  };
}


class FindbarView {
  viewer: PDFViewerApplicationClass;

  opened = false;

  constructor(viewer: PDFViewerApplicationClass) {
    this.viewer = viewer;

    this.viewer.config.findBar.findClose.addEventListener('click', () => this.close());
    this.viewer.config.findBar.findPrevious.addEventListener('click', () => this.dispatchEvent('again', true));
    this.viewer.config.findBar.findNext.addEventListener('click', () => this.dispatchEvent('again', false));
    this.viewer.config.findBar.findInput.addEventListener('input', () => this.dispatchEvent(''));
    this.viewer.config.findBar.findbar.addEventListener('keydown', (e: KeyboardEvent) => {
      if (e.key === 'Enter') {
        this.dispatchEvent('again', e.shiftKey);
      } else if (e.key === 'Escape') {
        this.close();
      }
    });

    this.viewer.eventBus.on('updatefindmatchescount', (e: FindUpdateEvent) => this.updateResultsCount(e));
    this.viewer.eventBus.on('updatefindcontrolstate', (e: FindUpdateEvent) => this.updateUIState(e));
  }

  open() {
    this.opened = true;

    this.viewer.config.findBar.findbar.classList.remove('hidden');
    this.viewer.config.findBar.findInput.select();
    this.viewer.config.findBar.findInput.focus();
  }

  close() {
    this.opened = false;
    this.viewer.eventBus.dispatch('findbarclose', { source: this });

    this.viewer.config.findBar.findbar.classList.add('hidden');
  }

  dispatchEvent(type: string, findPrevious = false) {
    this.viewer.eventBus.dispatch("find", {
      source: this,
      type,
      query: this.viewer.config.findBar.findInput.value,
      caseSensitive: false,
      entireWord: false,
      highlightAll: true,
      findPrevious,
      matchDiacritics: false,
    });
  }

  updateResultsCount(e: FindUpdateEvent) {
    const findResultsCount = this.viewer.config.findBar.findResultsCount;
    /* if (e.matchesCount.total > MAX_MATCHES_COUNT) {
      findResultsCount.textContent = `>${MAX_MATCHES_COUNT} results`;
    } else */ if (e.matchesCount.total > 0) {
      findResultsCount.textContent = `${e.matchesCount.current} of ${e.matchesCount.total}`;
    } else {
      findResultsCount.textContent = '';
    }
  }

  updateUIState(e: FindUpdateEvent) {
    let findMsg = '';
    if (e.state === FindState.NOT_FOUND) {
      findMsg = 'No results';
    }
    this.viewer.config.findBar.findMsg.textContent = findMsg;
    this.viewer.config.findBar.findInput.setAttribute('data-status', e.state === FindState.PENDING ? 'pending' : '');

    this.updateResultsCount(e);
  }
}


class PDFViewerApplicationClass {
  config: PDFViewerApplicationConfig;

  pdfLoadingTask: PDFDocumentLoadingTask | null = null;
  pdfDocument: PDFDocumentProxy | null = null;
  pdfViewer: PDFViewer;
  linkService: PDFLinkService;
  eventBus: EventBus;
  l10n: GenericL10n;
  downloadManager: DownloadManager;
  findController: PDFFindController;
  touchManager: TouchManager;

  findbarView: FindbarView;
  _isCtrlKeyDown = false;
  _wheelUnusedTicks = 0;
  _wheelUnusedFactor = 0;
  _touchUnusedFactor = 0;

  /**
   * Constructor that initializes the UI elements for the PDF viewer
   */
  constructor(config: PDFViewerApplicationConfig) {
    this.config = config;

    this.eventBus = new EventBus();
    this.linkService = new PDFLinkService({
      eventBus: this.eventBus,
      externalLinkTarget: LinkTarget.BLANK,
    });
    this.downloadManager = new DownloadManager();
    this.findController = new PDFFindController({
      linkService: this.linkService,
      eventBus: this.eventBus,
      updateMatchesCountOnProgress: true,
    });
    const abortController = new AbortController();
    this.touchManager = new TouchManager({
      container: window,
      onPinching: this.touchPinchCallback as any,
      onPinchEnd: this.touchPinchEndCallback as any,
      signal: abortController.signal,
    });
    
    this.l10n = new GenericL10n('en-us');
    this.pdfViewer = new PDFViewer({
      container: config.mainContainer,
      viewer: config.viewerContainer,

      eventBus: this.eventBus,
      linkService: this.linkService,
      l10n: this.l10n,
      downloadManager: this.downloadManager,
      findController: this.findController,

      textLayerMode: 1,  // TextLayerMode.ENABLE,
      annotationMode: 1,  // AnnotationMode.ENABLE,
      annotationEditorMode: 0,  // AnnotationEditorType.NONE,

      supportsPinchToZoom: true,
    });
    this.linkService.setViewer(this.pdfViewer);

    this.findbarView = new FindbarView(this);

    config.toolbar.zoomIn.addEventListener("click", () => this.updateZoom(1));
    config.toolbar.zoomOut.addEventListener("click", () => this.updateZoom(-1));
    config.toolbar.scaleSelect.addEventListener("change", () => {
      this.pdfViewer.currentScaleValue = config.toolbar.scaleSelect.value;
    });
    config.toolbar.pageNumber.addEventListener("click", () => config.toolbar.pageNumber.select());
    config.toolbar.pageNumber.addEventListener("change", () => {
      this.page = parseInt(config.toolbar.pageNumber.value);

      // Ensure that the page number input displays the correct value,
      // even if the value entered by the user was invalid
      // (e.g. a floating point number).
      if (config.toolbar.pageNumber.value !== this.page.toString()) {
        config.toolbar.pageNumber.value = this.page.toString();
      }
    });
    config.appContainer.addEventListener("wheel", (e) => this.handleMouseWheel(e), { passive: false });
    config.appContainer.addEventListener("keydown", (e) => {
      let handled = false;
      if (e.key === 'Control') {
        this._isCtrlKeyDown = true;
      }
      if (e.ctrlKey) {
        if (['+', 'NumpadAdd', 'Equal'].includes(e.key)) {
          this.updateZoom(1);
          handled = true;
        } else if (['-', 'Minus', 'NumpadSubtract'].includes(e.key)) {
          this.updateZoom(-1);
          handled = true;
        } else if (['0', 'Digit0', 'Numpad0'].includes(e.key)) {
          this.pdfViewer.currentScaleValue = DEFAULT_SCALE_VALUE;
          handled = true;
        } else if (e.key === 'f') {
          this.findbarView.open();
          handled = true;
        } else if (e.key === 's') {
          this.download();
          handled = true;
        }
      } else if (!e.ctrlKey && !e.metaKey && !e.altKey && !e.shiftKey) {
        if (
          (e.key === 'ArrowLeft' && !this.pdfViewer.isHorizontalScrollbarEnabled) ||
          e.key === 'k' ||
          e.key === 'p'
        ) {
          this.pdfViewer.previousPage();
          handled = true;
        } else if (
          (e.key === 'ArrowRight' && !this.pdfViewer.isHorizontalScrollbarEnabled) ||
          e.key === 'j' ||
          e.key === 'n'
        ) {
          this.pdfViewer.nextPage();
          handled = true;
        }
      }

      if (handled) {
        e.preventDefault();
      }
    });
    window.addEventListener("keyup", (e) => {
      if (e.key === 'Control') {
        this._isCtrlKeyDown = false;
      }
    });
    window.addEventListener("resize", () => this.eventBus.dispatch('resize', { source: window }));

    config.toolbar.download.addEventListener("click", () => this.download());

    this.eventBus.on("pagesinit", () => {
      // We can use pdfViewer now, e.g. let's change default scale.
      this.pdfViewer.currentScaleValue = DEFAULT_SCALE_VALUE;
      
      // Update the total number of pages display
      this.config.toolbar.numPages.textContent = `/ ${this.pagesCount}`;
    });
    this.eventBus.on("pagechanging", (e: { pageNumber: number }) => {
      // Update the page number input field and buttons
      config.toolbar.pageNumber.value = e.pageNumber.toString();
    }, true);
    this.eventBus.on("scalechanging", (e: { scale: number, presetValue?: string }) => {
      // Listen for scale changes to update the customScaleOption
      const customScaleOption = config.toolbar.customScaleOption;
      const scaleSelect = config.toolbar.scaleSelect;
      
      if (e.presetValue) {
        // If using a preset value like 'auto', 'page-width', etc.
        scaleSelect.value = e.presetValue;
      } else {
        // Using a custom scale - update the custom option text and select it
        const percent = Math.round(e.scale * 100);
        customScaleOption.textContent = `${percent}%`;
        customScaleOption.value = String(percent);
        scaleSelect.value = customScaleOption.value;
      }
    });
    this.eventBus.on("namedaction", (e: { action: string }) => {
      if (e.action === 'Find') {
        this.findbarView.open();
      } else if (e.action === 'GoToPage') {
        this.config.toolbar.pageNumber.select();
      } else if (e.action === 'SaveAs') {
        this.download();
      }
    });
    this.eventBus.on("resize", () => {
      const currentScaleValue = this.pdfViewer.currentScaleValue;
      if (['auto', 'page-fit', 'page-width'].includes(currentScaleValue)) {
        this.pdfViewer.currentScaleValue = currentScaleValue;
      }
      this.pdfViewer.update();
    })
  }

  /**
   * Downloads the current PDF document.
   */
  async download() {
    if (!this.pdfDocument) {
      return;
    }
    
    // Use the downloadManager to handle the download
    const data = await this.pdfDocument.getData()
    this.downloadManager.download(data, null, 'document.pdf');
  }

  /**
   * Opens PDF document.
   */
  async open(args: { data: Uint8Array }): Promise<void> {
    const scrollInfo = {...this.pdfViewer._location};

    if (this.pdfLoadingTask) {
      // We need to destroy already opened document
      await this.close();
    }

    // Loading document.
    this.pdfLoadingTask = getDocument({
      ...args,
      isEvalSupported: false,
      disableAutoFetch: true,
      useWasm: false,
    });

    if (scrollInfo && Object.entries(scrollInfo).length > 0) {
      // Restore scroll position and zoom level of previous document
      this.eventBus.on('pagesinit', () => {
        try {
          this.linkService.setHash(`page=${Math.min(scrollInfo.pageNumber || 1, this.pagesCount)}&zoom=${scrollInfo.scale || DEFAULT_SCALE_VALUE},${scrollInfo.left || 0},${scrollInfo.top || 0}`);
        } catch {}
      }, {once: true});
    }

    try {
      const pdfDocument = await this.pdfLoadingTask.promise;
      // Document loaded, specifying document for the viewer.
      this.pdfDocument = pdfDocument;
      this.pdfViewer.setDocument(pdfDocument);
      this.linkService.setDocument(pdfDocument);
    } catch (err) {
      let key = "pdfjs-loading-error";
      const reason = err as Error;
      
      if (reason instanceof InvalidPDFException) {
        key = "pdfjs-invalid-file-error";
      }
      
      const msg = await this.l10n.get(key, null, reason?.message);
      this.error(msg, { message: reason?.message });
    }
  }

  /**
   * Closes opened PDF document.
   */
  async close() {
    if (!this.pdfLoadingTask) {
      return;
    }

    const promise = this.pdfLoadingTask.destroy();
    this.pdfLoadingTask = null;

    if (this.pdfDocument) {
      this.pdfDocument = null;

      this.pdfViewer!.setDocument(null as unknown as PDFDocumentProxy);
      this.linkService!.setDocument(null, null);
    }

    return await promise;
  }

  /**
   * Display an error message
   */
  error(message: string, moreInfo?: { message?: string, stack?: string, filename?: string, lineNumber?: number }) {
    const moreInfoText = [
      `PDF.js v${pdfjsVersion} (build: ${pdfjsBuild})`,
    ];
    if (moreInfo) {
      moreInfoText.push(`Message: ${moreInfo.message}`);

      if (moreInfo.stack) {
        moreInfoText.push(`Stack: ${moreInfo.stack}`);
      } else {
        if (moreInfo.filename) {
          moreInfoText.push(`File: ${moreInfo.filename}`);
        }
        if (moreInfo.lineNumber) {
          moreInfoText.push(`Line: ${moreInfo.lineNumber}`);
        }
      }
    }

    console.error(`${message}\n\n${moreInfoText.join("\n")}`);
  }

  /**
   * Get the total number of pages in the PDF
   */
  get pagesCount() {
    return this.pdfDocument?.numPages || 0;
  }

  /**
   * Get the current page number
   */
  get page() {
    return this.pdfViewer.currentPageNumber;
  }

  /**
   * Set the current page number
   */
  set page(val: number) {
    this.pdfViewer.currentPageNumber = Math.max(1, Math.min(val, this.pagesCount));
  }

  updateZoom(steps?: number, scaleFactor?: number, origin?: number[]) {
    this.pdfViewer.updateScale({
      drawingDelay: 400,
      steps,
      scaleFactor,
      origin,
    });
  }

  /**
   * Handles mouse wheel events for zooming when Ctrl key is pressed
   */
  handleMouseWheel(event: WheelEvent): void {
    // It is important that we query deltaMode before delta{X,Y}, so that
    // Firefox doesn't switch to DOM_DELTA_PIXEL mode for compat with other
    // browsers, see https://bugzilla.mozilla.org/show_bug.cgi?id=1392460.
    const deltaMode = event.deltaMode;

    // The following formula is a bit strange but it comes from:
    // https://searchfox.org/mozilla-central/rev/d62c4c4d5547064487006a1506287da394b64724/widget/InputData.cpp#618-626
    let scaleFactor = Math.exp(-event.deltaY / 100);

    const isBuiltInMac = navigator.platform?.toUpperCase().includes('MAC');
    const isPinchToZoom =
      event.ctrlKey &&
      !this._isCtrlKeyDown &&
      deltaMode === WheelEvent.DOM_DELTA_PIXEL &&
      event.deltaX === 0 &&
      (Math.abs(scaleFactor - 1) < 0.05 || isBuiltInMac) &&
      event.deltaZ === 0;
    const origin = [event.clientX, event.clientY];

    if (
      isPinchToZoom ||
      event.ctrlKey ||
      event.metaKey
    ) {
      // Only zoom the pages, not the entire viewer.
      event.preventDefault();

      if (isPinchToZoom) {
        scaleFactor = this._accumulateFactor(this.pdfViewer.currentScale, scaleFactor, '_wheelUnusedFactor');
        this.updateZoom(undefined, scaleFactor, origin);
      } else {
        // Get delta and determine zoom direction
        const delta = this.normalizeWheelEventDirection(event);

        let ticks = 0;
        if (deltaMode === WheelEvent.DOM_DELTA_LINE || WheelEvent.DOM_DELTA_PAGE) {
          // For line-based devices, use one tick per event, because different
          // OSs have different defaults for the number lines. But we generally
          // want one "clicky" roll of the wheel (which produces one event) to
          // adjust the zoom by one step.
          //
          // If we're getting fractional lines (I can't think of a scenario
          // this might actually happen), be safe and use the accumulator.
          ticks = Math.abs(delta) >= 1 ? Math.sign(delta) : this._accumulateTicks(delta);
        } else {
          // pixel-based devices
          const PIXELS_PER_LINE_SCALE = 30;
          ticks = this._accumulateTicks(delta / PIXELS_PER_LINE_SCALE);
        }

        this.updateZoom(ticks, undefined, origin);
      }
    }
  }

  touchPinchCallback(origin: number[], prevDistance: number, distance: number) {
    const newScaleFactor = this._accumulateFactor(
      this.pdfViewer.currentScale,
      distance / prevDistance,
      "_touchUnusedFactor"
    );
    this.updateZoom(undefined, newScaleFactor, origin);
  }

  touchPinchEndCallback() {
    this._touchUnusedFactor = 1;
  }

  normalizeWheelEventDirection(evt: WheelEvent): number {
    let delta = Math.hypot(evt.deltaX, evt.deltaY);
    const angle = Math.atan2(evt.deltaY, evt.deltaX);
    if (-0.25 * Math.PI < angle && angle < 0.75 * Math.PI) {
      // All that is left-up oriented has to change the sign.
      delta = -delta;
    }
    return delta;
  }

  _accumulateTicks(ticks: number) {
    // If the direction changed, reset the accumulated ticks.
    if ((this._wheelUnusedTicks > 0 && ticks < 0) || (this._wheelUnusedTicks < 0 && ticks > 0)) {
      this._wheelUnusedTicks = 0;
    }
    this._wheelUnusedTicks += ticks;
    const wholeTicks = Math.trunc(this._wheelUnusedTicks);
    this._wheelUnusedTicks -= wholeTicks;
    return wholeTicks;
  }

  _accumulateFactor(previousScale: number, factor: number, prop: '_wheelUnusedFactor'|'_touchUnusedFactor' = '_wheelUnusedFactor') {
    if (factor === 1) {
      return 1;
    }

    // If the direction changed, reset the accumulated factor.
    if ((this[prop] > 1 && factor < 1) || (this[prop] < 1 && factor > 1)) {
      this[prop] = 1;
    }

    const newFactor = Math.floor(previousScale * factor * this[prop] * 100) / (100 * previousScale);
    this[prop] = factor / newFactor;

    return newFactor;
  }
}

function webViewerLoad() {
  // Create a singleton instance
  const PDFViewerApplication = new PDFViewerApplicationClass({
    appContainer: document.body,
    mainContainer: document.getElementById('viewerContainer') as HTMLDivElement,
    viewerContainer: document.getElementById('viewer') as HTMLDivElement,
    toolbar: {
      zoomIn: document.getElementById('zoomIn') as HTMLButtonElement,
      zoomOut: document.getElementById('zoomOut') as HTMLButtonElement,
      scaleSelect: document.getElementById('scaleSelect') as HTMLSelectElement,
      customScaleOption: document.getElementById('customScaleOption') as HTMLOptionElement,
      pageNumber: document.getElementById('pageNumber') as HTMLInputElement,
      numPages: document.getElementById('numPages') as HTMLElement,
      download: document.getElementById('download') as HTMLButtonElement,
    },
    findBar: {
      findbar: document.getElementById('findbar') as HTMLElement,
      findInput: document.getElementById('findInput') as HTMLInputElement,
      findResultsCount: document.getElementById('findResultsCount') as HTMLElement,
      findMsg: document.getElementById('findMsg') as HTMLElement,
      findPrevious: document.getElementById('findPrevious') as HTMLButtonElement,
      findNext: document.getElementById('findNext') as HTMLButtonElement,
      findClose: document.getElementById('findClose') as HTMLButtonElement,
    }
  });
  // Make PDFViewerApplication globally available
  (window as any).PDFViewerApplication = PDFViewerApplication;

  // Load PDFs via postMessage
  window.addEventListener('message', async (msg) => {
    if (msg.origin !== window.origin) {
      return;
    }

    // Load PDF
    await PDFViewerApplication.open({ data: msg.data as Uint8Array });
  });
}


if (document.readyState === "interactive" || document.readyState === "complete") {
  webViewerLoad();
} else {
  document.addEventListener("DOMContentLoaded", webViewerLoad, true);
}