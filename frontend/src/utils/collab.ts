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

export function useCollab(storeState: CollabStoreState<any>) {
  const eventBusUpdateKey = useEventBus('collab.update_key');
  const eventBusUpdateText = useEventBus('collab.update_text');

  // TODO: handle update_text events in store instead of codemirror
  // * codemirror: only emit @collab events (via default vue event mechanism or eventBus?)
  // * store: add update to per-path unconfirmedUpdates
  // * store: apply update to local data
  // * store: send (throttled) update to websocket
  // * server: process update, update version, broadcast to all clients
  // * store: receive update from websocket
  // * store: remove from unconfirmedUpdates (similar logic to codemirror receiveUpdates)
  // implementation notes notes:
  // * codemirror undo/redo: how to differentiate between local and remote changes? => send event from store to codemirror (via event bus) for changes from websocket with remote: true/false, right before applying update in store
  // * how to store awareness information: cursor, selection, etc. => separate data structure store for awareness infos
  // * on connect: clear unconfirmedUpdates, fetch initial data from server

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
        storeState.websocketSendThrottle.set(dataPath, throttle(sendUpdateWebsocket, 200, { leading: false, trailing: true }));
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
