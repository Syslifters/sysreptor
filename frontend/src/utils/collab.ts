import set from "lodash/set";
import unset from "lodash/unset";
import throttle from "lodash/throttle";
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
  handleAdditionalWebSocketMessages?: (event: any) => boolean
  websocketSendThrottle: Map<string, (msg: string) => void>;
  version: number;
}

export function makeCollabStoreState<T>(options: {
  websocketPath: string, 
  initialData: T,
  handleAdditionalWebSocketMessages?: (event: any) => boolean
}): CollabStoreState<T> {
  return {
    data: options.initialData,
    websocketPath: options.websocketPath,
    handleAdditionalWebSocketMessages: options.handleAdditionalWebSocketMessages,
    connectionState: CollabConnectionState.CLOSED,
    websocket: null,
    websocketSendThrottle: new Map(),
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

  // TODO: on initial connection failed (or permission denied): fetch list via REST API and set readonly

  function connect() {
    if (storeState.connectionState !== CollabConnectionState.CLOSED) {
      return;
    }
  
    const serverUrl = import.meta.env.DEV ? 
      'ws://localhost:8000' : 
      `${window.location.protocol === 'https' ? 'wss' : 'ws'}://${window.location.host}/`;
    const wsUrl = urlJoin(serverUrl, storeState.websocketPath);
    console.log('useCollab.connect websocket', wsUrl);
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
      if (msgData.version && msgData.version > storeState.version) {
        storeState.version = msgData.version;
      }
      if (msgData.type === 'init') {
        storeState.connectionState = CollabConnectionState.OPEN;
        storeState.data = msgData.data;
      } else if (msgData.type === 'collab.update_key') {
        eventBusUpdateKey.emit({
          ...msgData, 
          path: storeState.websocketPath + msgData.path, 
          source: 'ws',
        });
      } else if (msgData.type === 'collab.update_text') {
        eventBusUpdateText.emit({ 
          ...msgData, 
          path: storeState.websocketPath + msgData.path,
          source: 'ws',
        });
      } else if (msgData.type === 'collab.create') {
        set(storeState.data as Object, msgData.path, msgData.value);
      } else if (msgData.type === 'collab.delete') {
        unset(storeState.data as Object, msgData.path);
      } else if (!storeState.handleAdditionalWebSocketMessages?.(msgData)) {
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
    console.log('useCollab.disconnect websocket');
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
      sendUpdateWebsocket(JSON.stringify({
        type: 'collab.update_key',
        path: dataPath,
        value: event.value,
      }));
    }

    // Update local state
    set(storeState.data as Object, dataPath, event.value);
  }

  function updateText(event: any) {
    if (!event.path?.startsWith(storeState.websocketPath)) {
      // Event is not for us
      return;
    }
    const dataPath = toDataPath(event.path);
    if (event.source !== 'ws') {
      if (!storeState.websocketSendThrottle.has(dataPath)) {
        storeState.websocketSendThrottle.set(dataPath, throttle(sendUpdateWebsocket, 1000, { leading: false, trailing: true }));
      }

      // Propagate event to other clients
      storeState.websocketSendThrottle.get(dataPath)!(JSON.stringify({
        type: 'collab.update_text',
        path: dataPath,
        updates: event.updates,
      }));
    }

    // Updating text field content is handled in useMarkdownEditor
  }
  function sendUpdateWebsocket(msg: string) {
    console.log('sendUpdateWebsocket', msg);
    storeState.websocket?.send(msg);
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
