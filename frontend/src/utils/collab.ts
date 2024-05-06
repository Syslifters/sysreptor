import get from "lodash/get";
import set from "lodash/set";
import unset from "lodash/unset";
import throttle from "lodash/throttle";
import trimStart from "lodash/trimStart";
import urlJoin from "url-join";
import { ChangeSet, EditorSelection, Text } from "reportcreator-markdown/editor"
import { type UserShortInfo } from "@/utils/types"

const WS_RESPONSE_TIMEOUT = 5_000;
const WS_PING_INTERVAL = 30_000;
const WS_THROTTLE_INTERVAL_UPDATE_KEY = 1_000;
const WS_THROTTLE_INTERVAL_UPDATE_TEXT = 1_000;
const WS_THROTTLE_INTERVAL_AWARENESS = 1_000;
const HTTP_FALLBACK_INTERVAL = 10_000;

export enum CollabEventType {
  CONNECT = 'collab.connect',
  DISCONNECT = 'collab.disconnect',
  INIT = 'collab.init',
  CREATE = 'collab.create',
  UPDATE_KEY = 'collab.update_key',
  UPDATE_TEXT = 'collab.update_text',
  DELETE = 'collab.delete',
  SORT = 'collab.sort',
  AWARENESS = 'collab.awareness',
  ERROR = 'error',
  PING = 'ping',
};

export type TextUpdate = {
  changes: ChangeSet;
  selection?: EditorSelection;
}

export type CollabClientInfo = {
  client_id: string;
  client_color: string;
  user: UserShortInfo;
}

export type CollabEvent = {
  type: CollabEventType;
  path: string|null;
  version: number;
  client_id?: string;
  value?: any;
  updates?: (TextUpdate|{ changes: any, seletion?: any })[];
  selection?: any;
  update_awareness?: boolean;
  data?: any;
  client?: CollabClientInfo;
  clients?: CollabClientInfo[];
  permissions?: {
    read: boolean;
    write: boolean;
  }
}

export enum CollabConnectionType {
  WEBSOCKET = 'websocket',
  HTTP_FALLBACK = 'http_fallback',
  HTTP_READONLY = 'http_readonly',
};

export enum CollabConnectionState {
  CLOSED = 'closed',
  CONNECTING = 'connecting',
  INITIALIZING = 'initializing',
  OPEN = 'open',
};

export type CollabConnectionInfo = {
  type: CollabConnectionType;
  url: string;
  connectionState: CollabConnectionState;
  connectionError?: { error: any, message?: string };
  connect: () => Promise<void>;
  disconnect: () => Promise<void>;
  send: (msg: CollabEvent) => void;
};

export type CollabStoreState<T> = {
  data: T;
  apiPath: string;
  connection?: CollabConnectionInfo;
  handleAdditionalWebSocketMessages?: (event: CollabEvent, collabState: CollabStoreState<T>) => boolean;
  perPathState: Map<string, {
    unconfirmedTextUpdates: TextUpdate[];
  }>;
  awareness: {
    self: {
      path: string|null;
      selection?: EditorSelection;
    };
    other: {
      [key: string]: {
        client_id: string;
        path: string|null;
        selection?: EditorSelection;
      }
    };
    clients: CollabClientInfo[];
  },
  permissions: {
    read: boolean;
    write: boolean;
  },
  version: number;
  clientID: string;
}

export function makeCollabStoreState<T>(options: {
  apiPath: string, 
  initialData: T,
  initialPath?: string,
  handleAdditionalWebSocketMessages?: (event: CollabEvent, storeState: CollabStoreState<T>) => boolean
}): CollabStoreState<T> {
  return {
    data: options.initialData,
    apiPath: options.apiPath,
    handleAdditionalWebSocketMessages: options.handleAdditionalWebSocketMessages,
    perPathState: new Map(),
    awareness: {
      self: {
        path: options.initialPath || '',
      },
      other: {},
      clients: [],
    },
    permissions: {
      read: true,
      write: true,
    },
    version: 0,
    clientID: '',
  }
}

export function connectionWebsocket<T = any>(storeState: CollabStoreState<T>, onReceiveMessage: (msg: CollabEvent) => void) {
  const serverUrl = `${window.location.protocol === 'http:' ? 'ws' : 'wss'}://${window.location.host}/`;
  const wsUrl = urlJoin(serverUrl, storeState.apiPath);
  const websocket = ref<WebSocket|null>(null);
  const perPathState = new Map<string, {
    sendUpdateTextThrottled: ReturnType<typeof throttle>;
    sendUpdateKeyThrottled: ReturnType<typeof throttle>;
  }>();
  const sendAwarenessThrottled = throttle(websocketSendAwareness, WS_THROTTLE_INTERVAL_AWARENESS, { leading: false, trailing: true });

  const connectionInfo = reactive<CollabConnectionInfo>({
    type: CollabConnectionType.WEBSOCKET,
    url: wsUrl,
    connectionState: CollabConnectionState.CLOSED,
    connectionError: undefined,
    connect,
    disconnect,
    send,
  });

  const websocketConnectionLostTimeout = throttle(async () => {
    await nextTick();

    if (websocket.value && connectionInfo.connectionState !== CollabConnectionState.CLOSED) {
      // eslint-disable-next-line no-console
      console.error('Websocket connection timed out', storeState.apiPath);
    }
    websocket.value?.close(4504);
  }, WS_RESPONSE_TIMEOUT, { leading: false, trailing: true });

  function connect() {
    return new Promise<void>((resolve, reject) => {
      if (connectionInfo.connectionState !== CollabConnectionState.CLOSED) {
        resolve();
        return;
      }

      connectionInfo.connectionState = CollabConnectionState.CONNECTING;
      websocket.value = new WebSocket(wsUrl);
      websocket.value.addEventListener('open', () => {
        connectionInfo.connectionState = CollabConnectionState.INITIALIZING;
        websocketConnectionLossDetection();
      })
      websocket.value.addEventListener('close', (event) => {
        // Error handling
        if (event.code === 4443) {
          connectionInfo.connectionError = { error: event, message: event.reason || 'Permission denied' };
        } else if (connectionInfo.connectionState === CollabConnectionState.CONNECTING) {
          connectionInfo.connectionError = { error: event, message: event.reason || 'Failed to establish connection' };
        } else if (event.code === 4504) {
          // Possible reasons: network outage, browser tab becomes inactive, server crashes
          connectionInfo.connectionError = { error: event, message: event.reason || 'Connection timeout: Server connection lost' };
        } else if (event.code !== 1000) {
          connectionInfo.connectionError = { error: event, message: event.reason };
        }
        // eslint-disable-next-line no-console
        console.log('Websocket closed', event, connectionInfo.connectionError);
        
        // Reset data
        websocket.value = null;
        websocketConnectionLostTimeout.cancel();
        sendAwarenessThrottled?.cancel();
        for (const s of perPathState.values()) {
          s.sendUpdateTextThrottled.cancel();
        }
        storeState.perPathState?.clear();
        storeState.version = 0;
        connectionInfo.connectionState = CollabConnectionState.CLOSED;

        reject(connectionInfo.connectionError);
      });
      websocket.value.addEventListener('message', (event: MessageEvent) => {
        const msgData = JSON.parse(event.data) as CollabEvent;

        // Reset connection loss detection
        websocketConnectionLostTimeout?.cancel();
        
        // Handle message
        onReceiveMessage(msgData);

        // Promise result
        if (msgData.type === CollabEventType.INIT) {
          connectionInfo.connectionState = CollabConnectionState.OPEN;
          sendAwarenessThrottled();
          resolve();
        } else if (msgData.type === CollabEventType.UPDATE_KEY) {
          if (msgData.client_id !== storeState.clientID) {
            // Clear pending events of sub-fields
            for (const [k, v] of perPathState.entries()) {
              if (msgData.path === k || msgData.path?.startsWith(k + '.')) {
                v.sendUpdateTextThrottled.cancel();
              }
            }
          }
        } else if (msgData.type === CollabEventType.CONNECT) {
          if (msgData.client_id !== storeState.clientID) {
            // Send awareness info to new client
            sendAwarenessThrottled();
          }
        }
      });
    });
  }

  async function disconnect() {
    if ([WebSocket.CLOSED, WebSocket.CLOSING].includes(websocket.value?.readyState as any)) {
      return;
    }

    // Send all pending messages
    for (const s of perPathState.values()) {
      s.sendUpdateTextThrottled.flush();
    }
    await nextTick();

    websocket.value?.close(1000, 'Disconnect'); 
  }

  function send(msg: CollabEvent) {
    if (msg.type === CollabEventType.UPDATE_KEY) {
      if (msg.update_awareness) {
        // Awareness info is included in update_key message
        sendAwarenessThrottled?.cancel();
      }

      // Cancel pending update_key events of child fields
      for (const [k, v] of perPathState.entries()) {
        if (k.startsWith(msg.path + '.')) {
          v.sendUpdateKeyThrottled.cancel();
        }
      }
      
      // Throttle update_key messages
      const s = ensurePerPathState(msg.path!);
      s.sendUpdateKeyThrottled(msg);
    } else if (msg.type === CollabEventType.UPDATE_TEXT) {
      // Cancel pending awareness send: awareness info is included in the next update_text message
      sendAwarenessThrottled.cancel();
      // Throttle update_text messages
      const s = ensurePerPathState(msg.path!);
      s.sendUpdateTextThrottled();
    } else if (msg.type === CollabEventType.AWARENESS) {
      // Throttle awareness messages
      sendAwarenessThrottled();
    } else {
      websocketSend(msg);
    }
  }

  function websocketSend(msg: CollabEvent) {
    websocket.value?.send(JSON.stringify(msg));
    websocketConnectionLostTimeout();
  }

  function websocketSendAwareness() {
    if (!storeState.permissions.write) {
      return;
    }

    websocketSend({
      type: CollabEventType.AWARENESS,
      path: storeState.awareness.self.path,
      version: storeState.version,
      selection: storeState.awareness.self.selection?.toJSON(),
    });
  }

  function websocketSendUpdateText(path: string) {
    const updates = storeState.perPathState.get(path)?.unconfirmedTextUpdates.map(u => ({ changes: u.changes.toJSON() })) || [];
    if (updates.length === 0) {
      return;
    }

    let selection;
    if (storeState.awareness.self.path === path) {
      // Awareness info is included in update_text message
      // No need to send it separately
      selection = storeState.awareness.self.selection?.toJSON();
      sendAwarenessThrottled?.cancel();
    }

    websocketSend({
      type: CollabEventType.UPDATE_TEXT,
      path,
      version: storeState.version,
      updates,
      selection,
    });
  }

  function websocketSendUpdateKey(msg: CollabEvent) {
    websocketSend({
      ...msg,
      update_awareness: msg.update_awareness && msg.path === storeState.awareness.self.path,
    });
  }

  function ensurePerPathState(path: string) {
    if (!perPathState.has(path)) {
      perPathState.set(path, {
        sendUpdateTextThrottled: throttle(() => websocketSendUpdateText(path), WS_THROTTLE_INTERVAL_UPDATE_TEXT, { leading: false, trailing: true }),
        sendUpdateKeyThrottled: throttle((msg: CollabEvent) => websocketSendUpdateKey(msg), WS_THROTTLE_INTERVAL_UPDATE_KEY, { leading: true, trailing: true }),
      });
    }
    return perPathState.get(path)!;
  }

  async function websocketConnectionLossDetection() {
    const ws = websocket.value;
    while (connectionInfo.connectionState !== CollabConnectionState.CLOSED && websocket.value === ws) {
      await new Promise(resolve => setTimeout(resolve, WS_PING_INTERVAL));
      websocketSend({ 
        type: CollabEventType.PING,
        version: storeState.version,
        path: null,
      });
    }
  }

  return connectionInfo;
}

export function connectionHttpFallback<T = any>(storeState: CollabStoreState<T>, onReceiveMessage: (msg: CollabEvent) => void) {
  const httpUrl = urlJoin(storeState.apiPath, '/fallback/');
  const connectionInfo = reactive<CollabConnectionInfo>({
    type: CollabConnectionType.HTTP_FALLBACK,
    url: httpUrl,
    connectionState: CollabConnectionState.CLOSED,
    connectionError: undefined,
    connect,
    disconnect,
    send,
  });
  const pendingMessages = ref<CollabEvent[]>([]);
  const sendInterval = ref();

  async function connect() {
    try {
      const res = await $fetch<CollabEvent>(httpUrl, { method: 'GET' });
      onReceiveMessage(res);
      connectionInfo.connectionState = CollabConnectionState.OPEN;

      sendInterval.value = setInterval(sendPendingMessages, HTTP_FALLBACK_INTERVAL);
    } catch (e) {
      connectionInfo.connectionError = { error: e };
    }
  }

  async function disconnect() {
    clearInterval(sendInterval.value);
    sendInterval.value = undefined;

    await sendPendingMessages();

    storeState.perPathState?.clear();
    storeState.version = 0;
    connectionInfo.connectionState = CollabConnectionState.CLOSED;
  }

  function send(msg: CollabEvent) {
    if ([CollabEventType.AWARENESS, CollabEventType.PING, CollabEventType.UPDATE_TEXT].includes(msg.type)) {
      // Do not send.
      // collab.update_text is handled in sendPendingMessages
    } else {
      pendingMessages.value.push(msg);
    }
  }

  async function sendPendingMessages() {
    const messages = [...pendingMessages.value];
    for (const [p, s] of storeState.perPathState.entries()) {
      if (s.unconfirmedTextUpdates.length > 0) {
        messages.push({
          type: CollabEventType.UPDATE_TEXT,
          path: p,
          version: storeState.version,
          updates: s.unconfirmedTextUpdates.map(u => ({ changes: u.changes.toJSON() })),
        });
      }
    }

    const res = await $fetch<{ version: number, messages: CollabEvent[], clients: CollabClientInfo[] }>(httpUrl, { 
      method: 'POST', 
      body: {
        version: storeState.version,
        client_id: storeState.clientID,
        messages,
      }
    });
    for (const m of res.messages) {
      onReceiveMessage(m);
    }
    storeState.awareness.clients = res.clients;
    storeState.version = res.version;
    pendingMessages.value = [];
  }

  return connectionInfo;
}

export function connectHttpReadonly<T = any>(storeState: CollabStoreState<T>, onReceiveMessage: (msg: CollabEvent) => void) {
  const httpUrl = urlJoin(storeState.apiPath, '/fallback/');
  const connectionInfo = reactive<CollabConnectionInfo>({
    type: CollabConnectionType.HTTP_READONLY,
    url: httpUrl,
    connectionState: CollabConnectionState.CLOSED,
    connectionError: undefined,
    connect,
    disconnect: () => Promise.resolve(),
    send: () => {},
  });

  async function connect() {
    try {
      const res = await $fetch<CollabEvent>(httpUrl, { method: 'GET' });
      onReceiveMessage(res);
      connectionInfo.connectionState = CollabConnectionState.OPEN;
    } catch (e) {
      connectionInfo.connectionError = { error: e };
    }
  }

  return connectionInfo;
}

export function useCollab<T = any>(storeState: CollabStoreState<T>) {
  const eventBusBeforeApplyRemoteTextChange = useEventBus('collab:beforeApplyRemoteTextChanges');

  async function connect(options?: { connectionType?: CollabConnectionType }) {
    if (storeState.connection && storeState.connection.connectionState !== CollabConnectionState.CLOSED) {
      return;
    }

    storeState.perPathState?.clear();
    storeState.awareness = {
      self: { path: storeState.awareness.self.path },
      other: {},
      clients: [],
    }

    if (options?.connectionType === CollabConnectionType.HTTP_READONLY) {
      // HTTP read only connection
      storeState.connection = connectHttpReadonly(storeState, onReceiveMessage);
      return await storeState.connection?.connect();
    } else {
      // Try websocket connection first
      for (let i = 0; i < 2; i++) {
        try {
          storeState.connection = connectionWebsocket(storeState, onReceiveMessage);
          return await storeState.connection?.connect();
        } catch {}
      }

      // Fallback to HTTP polling
      storeState.connection = connectionHttpFallback(storeState, onReceiveMessage);
      return await storeState.connection?.connect();
    }
  }

  async function disconnect() {
    await storeState.connection?.disconnect();
  }

  function onReceiveMessage(msgData: CollabEvent) {  
    if (msgData.version && msgData.version > storeState.version) {
      storeState.version = msgData.version;
    }
    
    if (storeState.handleAdditionalWebSocketMessages?.(msgData, storeState)) {
      // Already handled
    } else if (msgData.type === CollabEventType.INIT) {
      storeState.data = msgData.data;
      storeState.clientID = msgData.client_id!;
      storeState.permissions = msgData.permissions!;
      storeState.awareness.clients = msgData.clients!;
      storeState.awareness.other = Object.fromEntries(msgData.clients!.filter((c: any) => c.client_id !== storeState.clientID).map((c: any) => [c.client_id, { 
        path: c.path, 
        selection: undefined, 
      }]));
    } else if (msgData.type === CollabEventType.UPDATE_KEY) {
      if (msgData.client_id !== storeState.clientID) {
      // Clear pending text updates, because they are overwritten by the value of collab.update_key
        for (const [k, v] of storeState.perPathState.entries()) {
          if (msgData.path === k || msgData.path!.startsWith(k + '.')) {
            v.unconfirmedTextUpdates = [];
          }
        }
    
        // Update local state
        set(storeState.data as Object, msgData.path!, msgData.value);
    
        removeInvalidSelections(msgData.path!);
      }
    } else if (msgData.type === CollabEventType.UPDATE_TEXT) {
      receiveUpdateText(msgData);
    } else if (msgData.type === CollabEventType.CREATE) {
      set(storeState.data as Object, msgData.path!, msgData.value);
    } else if (msgData.type === CollabEventType.DELETE) {
      const pathParts = msgData.path!.split('.');
      const parentPath = pathParts.slice(0, -1).join('.');
      const parentList = get(storeState.data as Object, parentPath);
      const parentListIndex = Number.parseInt(pathParts.slice(-1)?.[0].startsWith('[') ? pathParts.slice(-1)[0].slice(1, -1) : '');
              
      if (Array.isArray(parentList) && !Number.isNaN(parentListIndex)) {
        parentList!.splice(parentListIndex, 1);
      } else {
        unset(storeState.data as Object, msgData.path!);
      }
      removeInvalidSelections(parentPath);
    } else if (msgData.type === CollabEventType.CONNECT) {
      if (msgData.client_id !== storeState.clientID) {
        // Add new client
        storeState.awareness.clients.push(msgData.client!);
      }
    } else if (msgData.type === CollabEventType.DISCONNECT) {
      // Remove client
      storeState.awareness.clients = storeState.awareness.clients
        .filter(c => c.client_id !== msgData.client_id);
      delete storeState.awareness.other[msgData.client_id!];
    } else if (msgData.type === CollabEventType.AWARENESS) {
      if (msgData.client_id !== storeState.clientID) {
        storeState.awareness.other[msgData.client_id!] = {
          client_id: msgData.client_id!,
          path: msgData.path,
          selection: msgData.path ? parseSelection({
            selectionJson: msgData.selection, 
            unconfirmed: storeState.perPathState.get(msgData.path)?.unconfirmedTextUpdates || [], 
            text: get(storeState.data as Object, msgData.path) || ''
          }) : undefined,
        };
      }
    } else if (msgData.type === CollabEventType.ERROR) {
      // eslint-disable-next-line no-console
      console.error('Received error from websocket:', msgData);
    } else if (msgData.type === CollabEventType.PING) {
      // Do nothing
    } else {
      // eslint-disable-next-line no-console
      console.error('Received unknown websocket message:', msgData);
    }
  }

  function toDataPath(path: string) {
    return trimStart(path.slice(storeState.apiPath.length), '.');
  }

  function ensurePerPathState(path: string) {
    if (!storeState.perPathState.has(path)) {
      storeState.perPathState.set(path, {
        unconfirmedTextUpdates: [],
      });
    }
    return storeState.perPathState.get(path)!;
  }

  function updateKey(event: any) {
    if (!event.path?.startsWith(storeState.apiPath)) {
      // Event is not for us
      return;
    }

    // Update local state
    const dataPath = toDataPath(event.path);
    set(storeState.data as Object, dataPath, event.value);

    // Update awareness
    if (event.updateAwareness) {
      storeState.awareness.self = {
        path: dataPath,
        selection: undefined,
      };
    }

    // Propagate event to other clients
    storeState.connection?.send({
      type: event.type || CollabEventType.UPDATE_KEY,
      path: dataPath,
      version: storeState.version,
      value: event.value,
      update_awareness: event.updateAwareness,
    });
  }

  function createListItem(event: any) {
    if (!event.path?.startsWith(storeState.apiPath)) {
      // Event is not for us
      return;
    }

    // Do not update local state here. Wait for server event.
    // Propagate event to other clients
    const dataPath = toDataPath(event.path);
    storeState.connection?.send({
      type: CollabEventType.CREATE,
      path: dataPath,
      version: storeState.version,
      value: event.value,
    });
  }

  function deleteListItem(event: any) {
    if (!event.path?.startsWith(storeState.apiPath)) {
      // Event is not for us
      return;
    }

    // Do not update local state here. Wait for server event.
    // Propagate event to other clients
    const dataPath = toDataPath(event.path);
    storeState.connection?.send({
      type: CollabEventType.DELETE,
      path: dataPath,
      version: storeState.version,
    });
  }

  function updateText(event: any) {
    if (!event.path?.startsWith(storeState.apiPath)) {
      // Event is not for us
      return;
    }
    const dataPath = toDataPath(event.path);
    const perPathState = ensurePerPathState(dataPath);

    // Update local state
    const text = get(storeState.data as Object, dataPath) || '';
    let cmText = Text.of(text.split(/\r?\n/));
    let selection = storeState.awareness.self.path === dataPath ? storeState.awareness.self.selection : undefined;
    for (const u of event.updates) {
      // Apply text changes
      cmText = u.changes.apply(cmText);
      // Update local selection
      try {
        selection = selection?.map(u.changes);
      } catch {
        selection = undefined;
      }

      // Map selections of other clients onto changes
      for (const a of Object.values(storeState.awareness.other)) {
        if (a.path === dataPath) {
          try {
            a.selection = a.selection?.map(u.changes);
          } catch {
            a.selection = undefined;
          }
        }
      }
    }
    // Update text
    set(storeState.data as Object, dataPath, cmText.toString());

    // Update awareness
    storeState.awareness.self = {
      path: dataPath,
      selection,
    };

    // Track unconfirmed changes
    perPathState.unconfirmedTextUpdates.push(...event.updates.map((u: any) => ({
      changes: u.changes,
    })));

    // Propagate unconfirmed events to other clients
    storeState.connection?.send({
      type: CollabEventType.UPDATE_TEXT,
      path: dataPath,
      version: storeState.version,
      updates: perPathState.unconfirmedTextUpdates.map(u => ({ changes: u.changes.toJSON() })),
      selection: storeState.awareness.self.selection?.toJSON(),
    })
  }

  function updateAwareness(event: any) {
    if (!event.path?.startsWith(storeState.apiPath)) {
      // Event is not for us
      return;
    } else if (event.focus === false && event.path !== storeState.awareness.self.path) {
      // On focus other field: do not propagate unfocus event
      return;
    }

    const dataPath = toDataPath(event.path);
    if (storeState.awareness.self.path !== dataPath || storeState.awareness.self.selection !== event.selection) {
      storeState.awareness.self = {
        path: dataPath,
        selection: event.selection,
      };
      storeState.connection?.send({
        type: CollabEventType.AWARENESS,
        path: dataPath,
        version: storeState.version,
        selection: event.selection?.toJSON(),
      });
    }
  }

  function receiveUpdateText(event: any) {
    const perPathState = ensurePerPathState(event.path);
    let changes: ChangeSet|null = null;
    let version = storeState.version;
    let own = 0;
    for (const update of event.updates.map((u: any) => ({ changes: ChangeSet.fromJSON(u.changes) }))) {
      const ours = own < perPathState.unconfirmedTextUpdates.length ? perPathState.unconfirmedTextUpdates[own] : null;
      if (ours && storeState.clientID === event.client_id) {
        if (changes) {
          changes = changes.map(ours.changes, true);
        }
        own++;
      } else {
        changes = changes ? changes.compose(update.changes) : update.changes;
      }
      if (update.version > version) {
        version = update.version;
      }
    }

    let unconfirmed = perPathState.unconfirmedTextUpdates.slice(own)
    if (unconfirmed.length > 0) {
      if (changes) {
        unconfirmed = unconfirmed.map((update: any) => {
          const updateChanges = update.changes.map(changes!);
          changes = changes!.map(update.changes, true);
          return {
            changes: updateChanges,
          };
        });
      }
    }

    // Update store
    storeState.version = version;
    perPathState.unconfirmedTextUpdates = unconfirmed;

    if (changes) {
      // Send an event to the active markdown editor to apply changes before updating store state.
      // This allows the markdown editor to annotate the changes as remote change and handle it differently from local changes.
      // e.g. not add it to its local history to be able to only undo local changes, not remote changes of other users.
      eventBusBeforeApplyRemoteTextChange.emit({
        path: storeState.apiPath + event.path,
        changes,
      })

      // Apply changes to store state
      const text = get(storeState.data as Object, event.path) || '';
      let cmText = Text.of(text.split(/\r?\n/));
      cmText = changes.apply(cmText);
      set(storeState.data as Object, event.path, cmText.toString());

      // Update local selection
      if (storeState.awareness.self.path === event.path) {
        storeState.awareness.self.selection = storeState.awareness.self.selection?.map(changes);
      }
      
      // Update remote selections
      for (const a of Object.values(storeState.awareness.other)) {
        if (a.client_id === event.client_id) {
          a.path = event.path;
          if (event.selection) {
            a.selection = parseSelection({
              selectionJson: event.selection,
              unconfirmed,
              text: cmText,
            });
          }
        } else if (a.path === event.path) {
          a.selection = a.selection?.map(changes);
        }
      }
    }
  }

  function parseSelection(options: {selectionJson: any|undefined, unconfirmed: TextUpdate[], text: Text|string}) {
    if (!options.selectionJson) {
      return undefined;
    }
    try {
      let selection = EditorSelection.fromJSON(options.selectionJson);
      // Rebase selection onto unconfirmed changes
      for (const u of options.unconfirmed) {
        selection = selection.map(u.changes);
      }
      // Validate selection ranges are valid text positions
      for (const r of selection.ranges) {
        if (!(r.from >= 0 && r.to <= options.text.length)) {
          return undefined;
        }
      }
      return selection;
    } catch (e) {
      return undefined;
    }
  }

  function removeInvalidSelections(path?: string) {
    // Filter out invalid selections
    for (const a of [storeState.awareness.self].concat(Object.values(storeState.awareness.other))) {
      if (a.path && (!path || path === a.path || path.startsWith(a.path + '.')) && a.selection) {
        const text = get(storeState.data as Object, a.path);
        if (typeof text !== 'string' || !a.selection.ranges.every(r => r.from >= 0 && r.to <= (text || '').length)) {
          a.selection = undefined;
        }
      }
    }
  }

  function onCollabEvent(event: any) {
    if (!storeState.permissions.write) {
      return;
    }

    if (event.type === CollabEventType.UPDATE_KEY) {
      updateKey(event);
    } else if (event.type === CollabEventType.UPDATE_TEXT) {
      updateText(event);
    } else if (event.type === CollabEventType.CREATE) {
      createListItem(event);
    } else if (event.type === CollabEventType.DELETE) {
      deleteListItem(event);
    } else if (event.type === CollabEventType.AWARENESS) {
      updateAwareness(event);
    } else {
      // eslint-disable-next-line no-console
      console.error('Trying to send unknown collab event:', event);
    }
  }

  return {
    connect,
    disconnect,
    onCollabEvent,
    data: computed(() => storeState.data),
    readonly: computed(() => storeState.connection?.connectionState !== CollabConnectionState.OPEN || !storeState.permissions.write),
    connection: computed(() => storeState.connection),
    collabProps: computed(() => ({
      path: storeState.apiPath,
      clients: storeState.awareness.clients.map((c) => {
        const a = c.client_id === storeState.clientID ? 
          storeState.awareness.self : 
          storeState.awareness.other[c.client_id];
        return {
          ...c,
          path: storeState.apiPath + (a?.path || ''),
          selection: a?.selection,
          isSelf: c.client_id === storeState.clientID,
        };
      }),
    })),
  }
}

export type CollabPropType = {
  path: string;
  clients: {
    client_id: string;
    client_color: string;
    user: UserShortInfo;
    path: string;
    selection?: EditorSelection;
    isSelf: boolean;
  }[];
};

export function collabSubpath(collab: CollabPropType, subPath: string|null) {
  const addDot = !collab.path.endsWith('.') && !collab.path.endsWith('/') && subPath;
  const path = collab.path + (addDot ? '.' : '') + (subPath || '');
  return {
    ...collab,
    path,
    clients: collab.clients.filter(a => a.path.startsWith(path))
  };
}
