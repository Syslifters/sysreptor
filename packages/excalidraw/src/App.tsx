import { useEffect, useRef, useState } from "react";
import {
  Excalidraw,
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

