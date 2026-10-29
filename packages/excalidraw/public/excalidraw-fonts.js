// Rewrites font CDN URLs to self-hosted URLs. Needs to run before the Excalidraw bundle.
// https://github.com/excalidraw/excalidraw/issues/11639
(function () {
  window.EXCALIDRAW_ASSET_PATH = new URL('./', window.location.href).href;;

  const OriginalFontFace = window.FontFace;
  window.FontFace = class extends OriginalFontFace {
    constructor(family, source, descriptors) {
      if (typeof source === 'string' && source.includes('esm.sh/@excalidraw')) {
        source = source.replace(
          /https:\/\/esm\.sh\/@excalidraw\/excalidraw@[^/]+\/dist\/prod\//g,
          window.EXCALIDRAW_ASSET_PATH,
        );
      }
      super(family, source, descriptors);
    }
  };
})();
