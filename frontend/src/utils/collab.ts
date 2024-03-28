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
const WS_THROTTLE_INTERVAL_UPDATE_TEXT = 1_000;
const WS_THROTTLE_INTERVAL_AWARENESS = 1_000;

export enum CollabConnectionState {
  CLOSED = 'closed',
  CONNECTING = 'connecting',
  INITIALIZING = 'initializing',
  OPEN = 'open',
};

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
}

export type TextUpdate = {
  changes: ChangeSet;
  selection?: EditorSelection;
}

export type CollabStoreState<T> = {
  data: T;
  connectionState: CollabConnectionState;
  websocket: WebSocket|null;
  websocketPath: string;
  connectionError?: { error: any, message?: string };
  websocketConnectionLostTimeout?: ReturnType<typeof throttle>;
  handleAdditionalWebSocketMessages?: (event: any) => boolean;
  perPathState: Map<string, {
    sendUpdateTextThrottled: () => void;
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
        path: string;
        selection?: EditorSelection;
      }
    };
    clients: {
      client_id: string;
      client_color: string;
      user: UserShortInfo;
    }[];
    sendAwarenessThrottled?: ReturnType<typeof throttle<() => void>>;
  },
  version: number;
  clientID: string;
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
    perPathState: new Map(),
    awareness: {
      self: {
        path: 'notes',
      },
      other: {},
      clients: [],
    },
    version: 0,
    clientID: '',
  }
}

export function useCollab<T = any>(storeState: CollabStoreState<T>) {
  const eventBusBeforeApplyRemoteTextChange = useEventBus('collab:beforeApplyRemoteTextChanges');

  function connect() {
    return new Promise<void>((resolve, reject) => {
      if (storeState.connectionState !== CollabConnectionState.CLOSED) {
        resolve();
        return;
      }
    
      const serverUrl = `${window.location.protocol === 'http:' ? 'ws' : 'wss'}://${window.location.host}/`;
      const wsUrl = urlJoin(serverUrl, storeState.websocketPath);
      storeState.perPathState?.clear();
      storeState.awareness = {
        self: { path: storeState.awareness.self.path },
        other: {},
        clients: [],
        sendAwarenessThrottled: throttle(websocketSendAwareness, WS_THROTTLE_INTERVAL_AWARENESS, { leading: false, trailing: true })
      }
      storeState.connectionError = undefined;
      storeState.connectionState = CollabConnectionState.CONNECTING;
      storeState.websocket = new WebSocket(wsUrl);
      storeState.websocketConnectionLostTimeout = throttle(() => {
        if (storeState.websocket && storeState.connectionState !== CollabConnectionState.CLOSED) {
          // eslint-disable-next-line no-console
          console.error('Websocket connection timed out', storeState.websocketPath);
        }
        storeState.websocket?.close(4504);
      }, WS_RESPONSE_TIMEOUT, { leading: false, trailing: true });
      storeState.websocket.addEventListener('open', () => {
        storeState.connectionState = CollabConnectionState.INITIALIZING;
        websocketConnectionLossDetection();
      })
      storeState.websocket.addEventListener('close', (event) => {
        // Error handling
        if (event.code === 4443 || (event.code === 1006 && storeState.connectionState === CollabConnectionState.CONNECTING)) {
          storeState.connectionError = { error: event, message: event.reason || 'Permission denied' };
        } else if (storeState.connectionState === CollabConnectionState.CONNECTING) {
          storeState.connectionError = { error: event, message: event.reason || 'Failed to establish connection' };
        } else if (event.code === 4504) {
          // Possible reasons: network outage, browser tab becomes inactive, server crashes
          storeState.connectionError = { error: event, message: event.reason || 'Connection timeout: Server connection lost' };
        } else if (event.code !== 1000) {
          storeState.connectionError = { error: event, message: event.reason };
        }
        // eslint-disable-next-line no-console
        console.log('Websocket closed', event, storeState.connectionError);
        
        // Reset data
        storeState.websocket = null;
        storeState.websocketConnectionLostTimeout?.cancel();
        storeState.perPathState?.clear();
        storeState.version = 0;
        storeState.connectionState = CollabConnectionState.CLOSED;

        reject(storeState.connectionError);
      });
      storeState.websocket.addEventListener('message', (event: MessageEvent) => {
        const msgData = JSON.parse(event.data);

        // Reset connection loss detection
        storeState.websocketConnectionLostTimeout?.cancel();
  
        if (msgData.version && msgData.version > storeState.version) {
          storeState.version = msgData.version;
        }
        if (msgData.type === CollabEventType.INIT) {
          storeState.connectionState = CollabConnectionState.OPEN;
          storeState.data = msgData.data;
          storeState.clientID = msgData.client_id;
          storeState.awareness.clients = msgData.clients;
          storeState.awareness.other = Object.fromEntries(msgData.clients.filter((c: any) => c.client_id !== storeState.clientID).map((c: any) => [c.client_id, { 
            path: c.path, 
            selection: undefined, 
          }]));
          storeState.awareness.sendAwarenessThrottled?.();
          resolve();
        } else if (msgData.type === CollabEventType.UPDATE_KEY) {
          // Update local state
          set(storeState.data as Object, msgData.path, msgData.value);
        } else if (msgData.type === CollabEventType.UPDATE_TEXT) {
          receiveUpdateText(msgData);
        } else if (msgData.type === CollabEventType.UPDATE_KEY) {
          set(storeState.data as Object, msgData.path, msgData.value);
        } else if (msgData.type === CollabEventType.CREATE) {
          set(storeState.data as Object, msgData.path, msgData.value);
        } else if (msgData.type === CollabEventType.DELETE) {
          unset(storeState.data as Object, msgData.path);
        } else if (msgData.type === CollabEventType.CONNECT) {
          if (msgData.client_id !== storeState.clientID) {
            // Add new client
            storeState.awareness.clients.push(msgData);
            // Send awareness info to new client
            storeState.awareness.sendAwarenessThrottled?.();
          }
        } else if (msgData.type === CollabEventType.DISCONNECT) {
          // Remove client
          storeState.awareness.clients = storeState.awareness.clients
            .filter(c => c.client_id !== msgData.client_id);
          delete storeState.awareness.other[msgData.client_id];
        } else if (msgData.type === CollabEventType.AWARENESS) {
          if (msgData.client_id !== storeState.clientID) {
            storeState.awareness.other[msgData.client_id] = {
              client_id: msgData.client_id,
              path: msgData.path,
              selection: parseSelection({
                selectionJson: msgData.selection, 
                unconfirmed: storeState.perPathState.get(msgData.path)?.unconfirmedTextUpdates || [], 
                text: get(storeState.data as Object, msgData.path) || ''
              }),
            };
          }
        } else if (msgData.type === 'ping') {
          // Do nothing
        } else if (!storeState.handleAdditionalWebSocketMessages?.(msgData)) {
          // eslint-disable-next-line no-console
          console.error('Received unknown websocket message:', msgData);
        }
      });
    });
  }

  function disconnect() {
    storeState.websocket?.close(1000, 'Disconnect');
  }

  function websocketSend(msg: string) {
    storeState.websocket?.send(msg);
    storeState.websocketConnectionLostTimeout?.();
  }

  async function websocketConnectionLossDetection() {
    const ws = storeState.websocket;
    while (storeState.connectionState !== CollabConnectionState.CLOSED && storeState.websocket === ws) {
      await new Promise(resolve => setTimeout(resolve, WS_PING_INTERVAL));
      websocketSend(JSON.stringify({ type: 'ping' }));
    }
  }

  function websocketSendAwareness() {
    websocketSend(JSON.stringify({
      type: CollabEventType.AWARENESS,
      path: storeState.awareness.self.path,
      version: storeState.version,
      selection: storeState.awareness.self.selection?.toJSON(),
    }));
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
      storeState.awareness.sendAwarenessThrottled?.cancel();
    }

    websocketSend(JSON.stringify({
      type: CollabEventType.UPDATE_TEXT,
      path,
      version: storeState.version,
      updates,
      selection,
    }));
  }

  function toDataPath(path: string) {
    return trimStart(path.slice(storeState.websocketPath.length), '.');
  }

  function ensurePerPathState(path: string) {
    if (!storeState.perPathState.has(path)) {
      storeState.perPathState.set(path, {
        sendUpdateTextThrottled: throttle(() => websocketSendUpdateText(path), WS_THROTTLE_INTERVAL_UPDATE_TEXT, { leading: false, trailing: true }),
        unconfirmedTextUpdates: [],
      });
    }
    return storeState.perPathState.get(path)!;
  }

  function updateKey(event: any) {
    if (!event.path?.startsWith(storeState.websocketPath)) {
      // Event is not for us
      return;
    }

    // Update local state
    const dataPath = toDataPath(event.path);
    set(storeState.data as Object, dataPath, event.value);

    // Propagate event to other clients
    websocketSend(JSON.stringify({
      type: CollabEventType.UPDATE_KEY,
      path: dataPath,
      version: storeState.version,
      value: event.value,
    }));
  }

  function updateText(event: any) {
    if (!event.path?.startsWith(storeState.websocketPath)) {
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
      selection = selection?.map(u.changes);

      // Map selections of other clients onto changes
      for (const a of Object.values(storeState.awareness.other)) {
        if (a.path === dataPath) {
          a.selection = a.selection?.map(u.changes);
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
    // Cancel pending awareness send: awareness info is included in the next update_text message
    storeState.awareness.sendAwarenessThrottled?.cancel();

    // Track unconfirmed changes
    perPathState.unconfirmedTextUpdates.push(...event.updates.map((u: any) => ({
      changes: u.changes,
    })));

    // Propagate unconfirmed events to other clients
    perPathState.sendUpdateTextThrottled();
  }

  function updateAwareness(event: any) {
    if (!event.path?.startsWith(storeState.websocketPath)) {
      // Event is not for us
      return;
    } else if (event.focus === false && event.path !== storeState.awareness.self.path) {
      // On focus other field: do not propagate unfocus event
      return;
    }

    const dataPath = toDataPath(event.path);
    storeState.awareness.self = {
      path: dataPath,
      selection: event.selection,
    };

    storeState.awareness.sendAwarenessThrottled?.();
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
        path: storeState.websocketPath + event.path,
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

  function onCollabEvent(event: any) {
    if (event.type === CollabEventType.UPDATE_KEY) {
      updateKey(event);
    } else if (event.type === CollabEventType.UPDATE_TEXT) {
      updateText(event);
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
    updateKey,
    updateText,
    onCollabEvent,
    data: computed(() => storeState.data),
    connectionState: computed(() => storeState.connectionState),
    connectionError: computed(() => storeState.connectionError),
    collabProps: computed(() => ({
      path: storeState.websocketPath,
      clients: storeState.awareness.clients.map((c) => {
        const a = c.client_id === storeState.clientID ? 
          storeState.awareness.self : 
          storeState.awareness.other[c.client_id];
        return {
          ...c,
          path: storeState.websocketPath + (a?.path || ''),
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
