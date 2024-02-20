import set from "lodash/set";
import urlJoin from "url-join";
import { Connect } from "vite";

export enum CollabConnectionState {
  CLOSED = 'closed',
  CONNECTING = 'connecting',
  INITIALIZING = 'initializing',
  OPEN = 'open',
};

export type CollabState<T> = {
  websocket: WebSocket|null;
  connectionState: CollabConnectionState;
  clientId: string;
  version: number;
  // unconfirmedUpdates: any[];
  data: T;
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

export function useCollab<T>(path: string, initialData: T) {
  const websocket = ref<WebSocket|null>(null);
  const connectionState = ref(CollabConnectionState.CLOSED);
  const clientId = ref('');
  const version = ref(0);
  const data = ref(initialData);
  const observable = useObservable();
  
  function connect() {
    if (connectionState.value !== CollabConnectionState.CLOSED) {
      return;
    }
  
    const serverUrl = import.meta.env.DEV ? 
      'ws://localhost:8000' : 
      `${window.location.protocol === 'https' ? 'wss' : 'ws'}://${window.location.host}/`;
    const wsUrl = urlJoin(serverUrl, path);
    connectionState.value = CollabConnectionState.CONNECTING;
    websocket.value = new WebSocket(wsUrl);
    websocket.value.addEventListener('open', () => {
      connectionState.value = CollabConnectionState.INITIALIZING;
    })
    websocket.value.addEventListener('close', () => {
      connectionState.value = CollabConnectionState.CLOSED;
    });
    websocket.value.addEventListener('error', () => {
      connectionState.value = CollabConnectionState.CLOSED;
    });
    websocket.value.addEventListener('message', (event: MessageEvent) => {
      const data = JSON.parse(event.data);
      if (data.type === 'init') {
        connectionState.value = CollabConnectionState.OPEN;
        clientId.value = data.clientId;
        version.value = data.version;
        data.value = data.data;
      } else if (data.type === 'update.key') {
        // TODO: should we track unconfirmed updates, or is this irrelevant for update.key ?
        set(data.value as Object, data.path, data.value);
      } else if (data.type === 'update.text') {
        // TODO: handle in codemirror or here??
        observable.emit(data.type, data);
      } else {
        // eslint-disable-next-line no-console
        console.error('Received unknown websocket message:', data);
      }
    });
  }

  function disconnect() {
    if (connectionState.value === CollabConnectionState.CLOSED) {
      return;
    }
    websocket.value?.close();
    connectionState.value = CollabConnectionState.CLOSED;
    websocket.value = null;
  }

  function updateKey(path: string, value: any) {
    if (connectionState.value !== CollabConnectionState.OPEN) {
      return;
    }
  
    websocket.value!.send(JSON.stringify({
      type: 'update.key',
      path,
      value,
    }));
    set(data.value as Object, path, value);
  }

  return {
    clientId,
    connectionState,
    data,
    connect,
    disconnect,
    updateKey,
    on: observable.on,
    off: observable.off,
  }
}
