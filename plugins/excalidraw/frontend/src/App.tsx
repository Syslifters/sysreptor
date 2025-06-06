import { useEffect, useRef, useState } from "react";
import {
  Excalidraw,
  reconcileElements,
  useHandleLibrary,
} from "@excalidraw/excalidraw";
import { AppState, BinaryFiles, ExcalidrawInitialDataState } from "@excalidraw/excalidraw/types";
import { ExcalidrawImperativeAPI } from "@excalidraw/excalidraw/types";
import { RemoteExcalidrawElement } from "@excalidraw/excalidraw/data/reconcile";
import { OrderedExcalidrawElement } from "@excalidraw/excalidraw/element/types";
import { SysreptorCollab } from "./Collab";
import { useTheme } from "./utils";

import "@excalidraw/excalidraw/index.css";
import { LibraryIndexedDBAdapter } from "./store";

const PLUGIN_ID = 'c50b19ff-db68-4a83-9508-80ff6b6d2498';

function useResolvablePromise<T>() {
  let resolve: (value: T|PromiseLike<T>) => void;
  const promise = new Promise<T>((r) => { resolve = r; });
  return useRef<{
    promise: Promise<T>;
    resolve: (value: T|PromiseLike<T>) => void;
  }>({ promise, resolve: resolve! });
}


export default function App() {
  const projectId = new URLSearchParams(window.location.hash.slice(1)).get('projectId');
  const collabPath = `/api/plugins/${PLUGIN_ID}/ws/projects/${projectId}/excalidraw/`;
  const [excalidrawAPI, setExcalidrawAPI] = useState<ExcalidrawImperativeAPI|null>(null);
  const excalidrawCollabRef = useRef<SysreptorCollab | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [wasConnected, setWasConnected] = useState<boolean>(false);
  
  const loadInitialDataPromise = useResolvablePromise<ExcalidrawInitialDataState>();
  async function initializeScene(options: { excalidrawAPI: ExcalidrawImperativeAPI, excalidrawCollab: SysreptorCollab }): Promise<ExcalidrawInitialDataState> {
    if (!projectId) {
      throw new Error('No Project ID provided');
    }
    
    await options.excalidrawCollab.connect();
    const res = {
      elements: reconcileElements(
        options.excalidrawAPI.getSceneElementsIncludingDeleted(),
        options.excalidrawAPI.getSceneElementsIncludingDeleted() as RemoteExcalidrawElement[],
        options.excalidrawAPI.getAppState(),
      ),
      scrollToContent: true,
    };
    return res;
  }
  useEffect(() => {
    if (!excalidrawAPI || !excalidrawCollabRef.current) {
      return;
    }
    loadInitialDataPromise.current.resolve(initializeScene({
      excalidrawAPI,
      excalidrawCollab: excalidrawCollabRef.current,
    }));
  }, [excalidrawAPI, excalidrawCollabRef]);
  useEffect(() => {
    if (isConnected) {
      setWasConnected(true);
    } else if (!isConnected && wasConnected) {
      // Reload on connection loss.
      // An error message is shown when there is still a connection error after reload.
      window.location.reload();
    }
  }, [isConnected]);

  function onChange(elements: readonly OrderedExcalidrawElement[], appState: AppState, files: BinaryFiles) {
    excalidrawCollabRef.current?.syncElementsThrottled({ elements });
  }

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
        viewModeEnabled={!isConnected}
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
          <SysreptorCollab
            ref={excalidrawCollabRef}
            excalidrawAPI={excalidrawAPI}
            path={collabPath}
            onConnectionChange={setIsConnected}
          />
        )}
      </Excalidraw>
    </div>
  );
}

