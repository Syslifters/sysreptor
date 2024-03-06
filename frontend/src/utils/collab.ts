import set from "lodash/set";
import trimStart from "lodash/trimStart";
import urlJoin from "url-join";

export enum CollabConnectionState {
  CLOSED = 'closed',
  CONNECTING = 'connecting',
  INITIALIZING = 'initializing',
  OPEN = 'open',
};

export type CollabStoreState<T> = {
  data: T;
  connectionState: CollabConnectionState;
  websocket: WebSocket|null;
  websocketPath: string;
  version: number;
}

export function makeCollabStoreState<T>(websocketPath: string, data: T): CollabStoreState<T> {
  return {
    data,
    connectionState: CollabConnectionState.CLOSED,
    websocketPath,
    websocket: null,
    version: 0,
  }
}

export function useObservable() {
  const observers = new Map<string, Set<(event: unknown) => void>>();
  function on(name: string, callback: (event: unknown) => void) {
    if (!observers.has(name)) {
      observers.set(name, new Set());
    }
    observers.get(name)!.add(callback);
  }
  function off(name: string, callback: (event: unknown) => void) {
    if (!observers.has(name)) {
      return;
    }
    observers.get(name)!.delete(callback);
  }
  function emit(name: string, event: unknown) {
    if (!observers.has(name)) {
      return;
    }
    for (const callback of observers.get(name)!) {
      callback(event);
    }
  }

  return {
    on,
    off,
    emit,
  }
}

export function useCollab(storeState: CollabStoreState<any>) {
  const eventBusUpdateKey = useEventBus('collab.update_key');
  const eventBusUpdateText = useEventBus('collab.update_text');

  function connect() {
    if (storeState.connectionState !== CollabConnectionState.CLOSED) {
      return;
    }
  
    const serverUrl = import.meta.env.DEV ? 
      'ws://localhost:8000' : 
      `${window.location.protocol === 'https' ? 'wss' : 'ws'}://${window.location.host}/`;
    const wsUrl = urlJoin(serverUrl, storeState.websocketPath);
    storeState.connectionState = CollabConnectionState.CONNECTING;
    storeState.websocket = new WebSocket(wsUrl);
    storeState.websocket.addEventListener('open', () => {
      storeState.connectionState = CollabConnectionState.INITIALIZING;
    })
    storeState.websocket.addEventListener('close', () => {
      storeState.connectionState = CollabConnectionState.CLOSED;
    });
    storeState.websocket.addEventListener('error', () => {
      storeState.connectionState = CollabConnectionState.CLOSED;
    });
    storeState.websocket.addEventListener('message', (event: MessageEvent) => {
      const msgData = JSON.parse(event.data);
      console.log('Received websocket message:', msgData);
      if (msgData.type === 'init') {
        storeState.connectionState = CollabConnectionState.OPEN;
        storeState.version = msgData.version;
        storeState.data = msgData.data;
      } else if (msgData.type === 'collab.update_key') {
        // TODO: should we track unconfirmed updates, or is this irrelevant for collab.update_key ?
        eventBusUpdateKey.emit({
          ...msgData, 
          path: storeState.websocketPath + msgData.path, 
          source: 'ws',
        });
      } else if (msgData.type === 'collab.update_text') {
        // TODO: handle in codemirror or here??
        eventBusUpdateText.emit({ 
          ...msgData, 
          path: storeState.websocketPath + msgData.path,
          source: 'ws',
        });
      } else {
        // eslint-disable-next-line no-console
        console.error('Received unknown websocket message:', msgData);
      }
    });

    eventBusUpdateKey.on(updateKey);
    eventBusUpdateText.on(updateText);
  }

  function disconnect() {
    if (storeState.connectionState === CollabConnectionState.CLOSED) {
      return;
    }
    eventBusUpdateKey.off(updateKey);
    eventBusUpdateText.off(updateText);
    storeState.websocket?.close();
    storeState.connectionState = CollabConnectionState.CLOSED;
    storeState.websocket = null;
  }

  function toDataPath(path: string) {
    return trimStart(path.slice(storeState.websocketPath.length), '.');
  }

  function updateKey(event: any) {
    if (!event.path?.startsWith(storeState.websocketPath)) {
      // Event is not for us
      return;
    }

    const dataPath = toDataPath(event.path);
    if (event.source !== 'ws') {
      // Propagate event to other clients
      storeState.websocket?.send(JSON.stringify({
        type: 'collab.update_key',
        path: dataPath,
        value: event.value,
      }));
    }

    // Update local state
    console.log('collab.update_key', event);
    set(storeState.data as Object, dataPath, event.value);
  }

  function updateText(event: any) {
    if (!event.path?.startsWith(storeState.websocketPath)) {
      // Event is not for us
      return;
    }
    const dataPath = toDataPath(event.path);
    if (event.source !== 'ws') {
      // Propagate event to other clients
      storeState.websocket?.send(JSON.stringify({
        type: 'collab.update_text',
        path: dataPath,
        updates: event.updates,
      }));
    }

    // Updating text field content is handled in useMarkdownEditor
    console.log('collab.update_text', event);
  }

  return {
    connect,
    disconnect,
  }
}

export type CollabPropType = {
  path: string;
  version: number;
};

export function collabSubpath(collab: CollabPropType, subPath: string) {
  const addDot = !collab.path.endsWith('.') && !collab.path.endsWith('/');
  return {
    ...collab,
    path: collab.path + (addDot ? '.' : '') + subPath,
  }
}
