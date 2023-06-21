import * as pdfjsLib from 'pdfjs-dist/webpack';
import { PDFViewerApplication } from 'pdfjs-dist/lib/web/app';
import { DEFAULT_SCALE_VALUE, RenderingStates, ScrollMode, SpreadMode } from 'pdfjs-dist/lib/web/ui_utils';
import { LinkTarget } from 'pdfjs-dist/lib/web/pdf_link_service';
import { AppOptions } from 'pdfjs-dist/lib/web/app_options';
import GenericExternalServices from './com';
import './viewer.css';


PDFViewerApplication.externalServices = GenericExternalServices;
window.PDFViewerApplication = PDFViewerApplication;
window.PDFViewerApplicationConstants = { LinkTarget, RenderingStates, ScrollMode, SpreadMode };
window.PDFViewerApplicationOptions = AppOptions;

AppOptions.setAll({
  disablePreferences: true,
  workerPort: pdfjsLib.GlobalWorkerOptions.workerPort,
  defaultUrl: '',
  externalLinkTarget: LinkTarget.BLANK,
  enableScripting: false,
  pdfBugEnabled: false,
  disableAutoFetch: true,
  isEvalSupported: false,
  disableHistory: true,
  cursorToolOnLoad: 0,  // select
});

function getViewerConfiguration() {
  const disabled = document.getElementById('disabled');

  return {
    appContainer: document.body,
    mainContainer: document.getElementById("viewerContainer"),
    viewerContainer: document.getElementById("viewer"),
    toolbar: {
      container: document.getElementById("toolbarViewer"),
      numPages: document.getElementById("numPages"),
      pageNumber: document.getElementById("pageNumber"),
      scaleSelect: document.getElementById("scaleSelect"),
      customScaleOption: document.getElementById("customScaleOption"),
      zoomIn: document.getElementById("zoomIn"),
      zoomOut: document.getElementById("zoomOut"),

      previous: disabled,
      next: disabled,
      print: disabled,
      download: disabled,
      viewFind: disabled,
      openFile: disabled,
      editorFreeTextButton: disabled,
      editorFreeTextParamsToolbar: disabled,
      editorInkButton: disabled,
    },
    findBar: {
      bar: document.getElementById("findbar"),
      toggleButton: document.getElementById("findToggle"),
      findField: document.getElementById("findInput"),
      findMsg: document.getElementById("findMsg"),
      findResultsCount: document.getElementById("findResultsCount"),
      findPreviousButton: document.getElementById("findPrevious"),
      findNextButton: document.getElementById("findNext"),
      
      highlightAllCheckbox: disabled,
      caseSensitiveCheckbox: disabled,
      matchDiacriticsCheckbox: disabled,
      entireWordCheckbox: disabled,
    },
    openFileInput: disabled,
  };
}


async function webViewerLoad() {
  const config = getViewerConfiguration();

  await PDFViewerApplication.initialize(config);
  PDFViewerApplication.appConfig.mainContainer.addEventListener('transitionend', (evt) => {
    if (evt.target === this) {
      PDFViewerApplication.eventBus.dispatch('resize', { source: this });
    }
  });

  window.addEventListener('message', async (msg) => {
    if (msg.origin !== window.origin) {
      return;
    }

    // Save current scroll and zoom position
    const scrollInfo = await PDFViewerApplication.store?.getMultiple({
      page: null,
      zoom: DEFAULT_SCALE_VALUE,
      scrollLeft: "0",
      scrollTop: "0",
    });

    // load PDF
    await PDFViewerApplication.open({ data: msg.data });

    // restore scroll position and zoom
    PDFViewerApplication.eventBus.on('pagesinit', () => {
      if (scrollInfo && scrollInfo.page !== null) {
        PDFViewerApplication.pdfLinkService.setHash(`page=${scrollInfo.page}&zoom=${scrollInfo.zoom},${scrollInfo.scrollLeft},${scrollInfo.scrollTop}`);
      }
    }, {once: true});
  });
}

document.blockUnblockOnload?.(true);

if (document.readyState === "interactive" || document.readyState === "complete") {
  webViewerLoad();
} else {
  document.addEventListener("DOMContentLoaded", webViewerLoad, true);
}

