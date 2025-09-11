import { useEffect, useRef, useState } from "react";
import {
  Excalidraw,
  MainMenu,
  reconcileElements,
  useHandleLibrary,
} from "@excalidraw/excalidraw";
import { AppState, BinaryFiles, ExcalidrawInitialDataState, ExcalidrawImperativeAPI } from "@excalidraw/excalidraw/types";
import { RemoteExcalidrawElement } from "@excalidraw/excalidraw/data/reconcile";
import { OrderedExcalidrawElement } from "@excalidraw/excalidraw/element/types";
import { useResolvablePromise, useTheme } from "./utils";

import "@excalidraw/excalidraw/index.css";
import { LibraryIndexedDBAdapter } from "./store";
import { ExcalidrawSysreptorCollab } from "./Collab";


function reload() {
  window.location.reload();
}

function toggleFullscreen() {
  window.parent.postMessage({ type: 'toggleFullscreen' }, window.origin);
}


export default function App() {
  const iframeParams = new URLSearchParams(window.location.hash.slice(1));
  const params = {
    apiUrl: iframeParams.get('apiUrl'),
    websocketUrl: iframeParams.get('websocketUrl'),
  }
  const [excalidrawAPI, setExcalidrawAPI] = useState<ExcalidrawImperativeAPI|null>(null);
  const collabRef = useRef<ExcalidrawSysreptorCollab | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [wasConnected, setWasConnected] = useState<boolean>(false);
  const [isReadonly, setIsReadonly] = useState<boolean>(false);

  const loadInitialDataPromise = useResolvablePromise<ExcalidrawInitialDataState>();
  async function initializeScene(): Promise<ExcalidrawInitialDataState> {
    if (!collabRef.current || !excalidrawAPI) {
      throw new Error("Collab adapter or Excalidraw API not initialized");
    }
    collabRef.current.connect();
    const res = {
      elements: reconcileElements(
        excalidrawAPI.getSceneElementsIncludingDeleted(),
        excalidrawAPI.getSceneElementsIncludingDeleted() as RemoteExcalidrawElement[],
        excalidrawAPI.getAppState(),
      ),
      scrollToContent: true,
    };
    return res;
  }
  useEffect(() => {
    if (!excalidrawAPI || !collabRef.current) {
      return;
    }
    loadInitialDataPromise.current.resolve(initializeScene());
  }, [excalidrawAPI, collabRef]);
  useEffect(() => {
    if (isConnected) {
      setWasConnected(true);
    } else if (!isConnected && wasConnected) {
      // Reload on connection loss.
      // An error message is shown when there is still a connection error after reload.
      reload();
    }
  }, [isConnected]);

  function onChange(elements: readonly OrderedExcalidrawElement[], appState: AppState, files: BinaryFiles) {
    collabRef.current?.syncElementsThrottled({ elements });
  }

  // TODO: handle library: pass through from top-level window to iframe (window.name, hash change)
  useHandleLibrary({
    excalidrawAPI,
    adapter: LibraryIndexedDBAdapter,
  });

  const { isDarkTheme } = useTheme();
  return (
    <div style={{ height: '100vh' }}>
      <Excalidraw
        excalidrawAPI={setExcalidrawAPI}
        initialData={loadInitialDataPromise.current.promise}
        onChange={onChange}
        isCollaborating={true}
        libraryReturnUrl={window.top!.location.origin + window.top!.location.pathname}
        detectScroll={false}
        langCode="en"
        autoFocus={true}
        viewModeEnabled={!isConnected || isReadonly}
        theme={isDarkTheme ? 'dark' : 'light'}
        UIOptions={{
          canvasActions: {
            toggleTheme: false,
            changeViewBackgroundColor: false,
          },
          tools: {
            image: false,
          },
        }}
      >
        <MainMenu>
          <MainMenu.DefaultItems.LoadScene />
          <MainMenu.DefaultItems.Export />
          <MainMenu.DefaultItems.SaveAsImage />
          <MainMenu.DefaultItems.SearchMenu />
          {document.fullscreenEnabled ? 
            <MainMenu.Item 
              onSelect={toggleFullscreen}
              icon={
                <svg xmlns="http://www.w3.org/2000/svg" focusable="false" role="img" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M5,5H10V7H7V10H5V5M14,5H19V10H17V7H14V5M17,14H19V19H14V17H17V14M10,17V19H5V14H7V17H10Z" />
                </svg>
              }
            >
              Fullscreen
            </MainMenu.Item>
            : null
          }
          <MainMenu.DefaultItems.Help />
          <MainMenu.DefaultItems.ClearCanvas />
        </MainMenu>

        {excalidrawAPI && (
          <ExcalidrawSysreptorCollab
            ref={collabRef}
            excalidrawAPI={excalidrawAPI}
            params={params}
            onConnectionChange={setIsConnected}
            onReadonlyChange={setIsReadonly}
          />
        )}
        {collabRef.current && !isConnected && (
          <div className="collab-connection-warning">
            Connection failed
            <button onClick={reload}>Reload</button>
          </div>
        )}
      </Excalidraw>
    </div>
  );
}

