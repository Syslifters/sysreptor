import get from "lodash/get";
import set from "lodash/set";
import unset from "lodash/unset";
import throttle from "lodash/throttle";
import trimStart from "lodash/trimStart";
import urlJoin from "url-join";
import { ChangeSet, EditorSelection, Text } from "reportcreator-markdown/editor"
import { type UserShortInfo } from "@/utils/types"

export enum CollabConnectionState {
  CLOSED = 'closed',
  CONNECTING = 'connecting',
  INITIALIZING = 'initializing',
  OPEN = 'open',
};

export type TextUpdate = {
  changes: ChangeSet;
  selection?: EditorSelection;
}

export type CollabStoreState<T> = {
  data: T;
  connectionState: CollabConnectionState;
  websocket: WebSocket|null;
  websocketPath: string;
  handleAdditionalWebSocketMessages?: (event: any) => boolean;
  perPathState: Map<string, {
    sendUpdateTextThrottled: (msg: string) => void;
    unconfirmedTextUpdates: TextUpdate[];
  }>;
  awareness: {
    local: {
      path: string|null;
      selection?: EditorSelection;
    };
    remote: {
      [key: string]: {
        client_id: string;
        path: string;
        selection?: EditorSelection;
      }
    };
    clients: {client_id: string; user: UserShortInfo; color: string;}[];
    sendAwarenessThrottled?: ReturnType<typeof throttle<(msg: string) => void>>;
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
      local: {
        path: 'notes',
      },
      remote: {},
      clients: [],
    },
    version: 0,
    clientID: '',
  }
}

export function useCollab(storeState: CollabStoreState<any>) {
  const eventBusBeforeApplyRemoteTextChange = useEventBus('collab:beforeApplyRemoteTextChanges');

  function connect() {
    if (storeState.connectionState !== CollabConnectionState.CLOSED) {
      return;
    }
  
    const serverUrl = `${window.location.protocol === 'http:' ? 'ws' : 'wss'}://${window.location.host}/`;
    const wsUrl = urlJoin(serverUrl, storeState.websocketPath);
    storeState.perPathState?.clear();
    storeState.awareness.local = { path: null };
    storeState.awareness = {
      local: { path: null },
      remote: {},
      clients: [],
      sendAwarenessThrottled: throttle(websocketSend, 1000, { leading: false, trailing: true })
    }
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
        storeState.clientID = msgData.client_id;
      } else if (msgData.type === 'collab.update_key') {
        // Update local state
        set(storeState.data as Object, msgData.path, msgData.value);
      } else if (msgData.type === 'collab.update_text') {
        receiveUpdateText(msgData);
      } else if (msgData.type === 'collab.create') {
        set(storeState.data as Object, msgData.path, msgData.value);
      } else if (msgData.type === 'collab.delete') {
        unset(storeState.data as Object, msgData.path);
      } else if (msgData.type === 'collab.connect') {
        // Add new client
        storeState.awareness.clients.push(msgData);
        if (msgData.client_id !== storeState.clientID) {
          // Immediately send own awareness information to new client
          storeState.awareness.sendAwarenessThrottled?.(JSON.stringify({
            type: 'collab.awareness',
            path: storeState.awareness.local.path,
            version: storeState.version,
            selection: storeState.awareness.local.selection?.toJSON(),
          }));
          storeState.awareness.sendAwarenessThrottled?.flush();
        }
      } else if (msgData.type === 'collab.disconnect') {
        // Remove client
        storeState.awareness.clients = storeState.awareness.clients.filter(c => c.client_id !== msgData.client_id);
      } else if (msgData.type === 'collab.awareness') {
        if (msgData.client_id !== storeState.clientID) {
          let selection = msgData.selection ? EditorSelection.fromJSON(msgData.selection) : undefined;
          if (selection) {
            // Map onto unconfirmedTextUpdates
            for (const u of storeState.perPathState.get(msgData.path)?.unconfirmedTextUpdates || []) {
              selection = selection.map(u.changes);
            }
          }
          storeState.awareness.remote[msgData.client_id] = {
            client_id: msgData.client_id,
            path: msgData.path,
            selection,
          };
        }
      } else if (!storeState.handleAdditionalWebSocketMessages?.(msgData)) {
        // eslint-disable-next-line no-console
        console.error('Received unknown websocket message:', msgData);
      }
    });
  }

  function disconnect() {
    if (storeState.connectionState === CollabConnectionState.CLOSED) {
      return;
    }
    storeState.websocket?.close();
    storeState.connectionState = CollabConnectionState.CLOSED;
    storeState.websocket = null;
    storeState.perPathState?.clear()
  }

  function websocketSend(msg: string) {
    storeState.websocket?.send(msg);
  }

  function toDataPath(path: string) {
    return trimStart(path.slice(storeState.websocketPath.length), '.');
  }

  function ensurePerPathState(path: string) {
    if (!storeState.perPathState.has(path)) {
      storeState.perPathState.set(path, {
        sendUpdateTextThrottled: throttle(websocketSend, 1000, { leading: false, trailing: true }),
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
      type: 'collab.update_key',
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
    let selection = storeState.awareness.local.path === dataPath ? storeState.awareness.local.selection : undefined;
    for (const u of event.updates) {
      // Apply text changes
      cmText = u.changes.apply(cmText);
      // Update local selection
      if (u.selection) {
        selection = u.selection;
        // Cancel pending awareness update => awareness info is included in the next collab.update_text message
        storeState.awareness.sendAwarenessThrottled?.cancel();
      } else {
        selection = selection?.map(u.changes);
      }
      // Map selections of other clients onto changes
      for (const remoteAwareness of Object.values(storeState.awareness.remote)) {
        if (remoteAwareness.path === dataPath) {
          remoteAwareness.selection = remoteAwareness.selection?.map(u.changes);
        }
      }
    }
    set(storeState.data as Object, dataPath, cmText.toString());
    storeState.awareness.local = {
      path: dataPath,
      selection,
    };

    // Track unconfirmed changes
    perPathState.unconfirmedTextUpdates.push(...event.updates.map((u: any) => ({
      changes: u.changes,
    })));

    // Propagate unconfirmed events to other clients
    perPathState.sendUpdateTextThrottled(JSON.stringify({
      type: 'collab.update_text',
      path: dataPath,
      version: storeState.version,
      updates: perPathState.unconfirmedTextUpdates.map(u => ({ changes: u.changes.toJSON(), selection: u.selection?.toJSON() })),
    }));
  }

  function updateAwareness(event: any) {
    if (!event.path?.startsWith(storeState.websocketPath)) {
      // Event is not for us
      return;
    } else if (event.focus === false && event.path !== storeState.awareness.local.path) {
      // On focus other field: do not propagate unfocus event
      return;
    }

    console.log('updateAwareness', event);
    const dataPath = toDataPath(event.path);
    storeState.awareness.local = {
      path: dataPath,
      selection: event.selection,
    };

    storeState.awareness.sendAwarenessThrottled?.(JSON.stringify({
      type: 'collab.awareness',
      path: dataPath,
      version: storeState.version,
      selection: event.selection,
    }));
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
      if (storeState.awareness.local.path === event.path) {
        storeState.awareness.local.selection = storeState.awareness.local.selection?.map(changes);
      }
      // Update remote selections
      for (const remoteAwareness of Object.values(storeState.awareness.remote)) {
        if (remoteAwareness.path === event.path) {
          remoteAwareness.selection = remoteAwareness.selection?.map(changes);
        }
      }
    }
  }

  function onCollabEvent(event: any) {
    if (event.type === 'collab.update_key') {
      updateKey(event);
    } else if (event.type === 'collab.update_text') {
      updateText(event);
    } else if (event.type === 'collab.awareness') {
      updateAwareness(event);
    } else {
      // eslint-disable-next-line no-console
      console.error('Trying to send unknown collab event:', event);
    }
  }

  watch(() => storeState.awareness.local, () => {
    // TODO: debug only
    console.log('awareness.local changed', storeState.awareness.local.path, storeState.awareness.local.selection?.toJSON());
  }, { deep: true });

  return {
    connect,
    disconnect,
    updateKey,
    updateText,
    onCollabEvent,
    data: computed(() => storeState.data),
    connectionState: computed(() => storeState.connectionState),
    collabProps: computed(() => ({
      path: storeState.websocketPath,
    })),
  }
}

export type CollabPropType = {
  path: string;
};

export function collabSubpath(collab: CollabPropType, subPath: string) {
  const addDot = !collab.path.endsWith('.') && !collab.path.endsWith('/');
  return {
    ...collab,
    path: collab.path + (addDot ? '.' : '') + subPath,
  }
}
