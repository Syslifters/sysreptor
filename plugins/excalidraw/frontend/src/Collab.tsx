import { PureComponent } from "react";
import { throttle } from "lodash-es";
import urlJoin from "url-join";

import { 
  hashElementsVersion,
  isInvisiblySmallElement, 
  reconcileElements, 
  restoreElements, 
  CaptureUpdateAction 
} from "@excalidraw/excalidraw";
import { ExcalidrawImperativeAPI } from "@excalidraw/excalidraw/types";
import { ExcalidrawElement, OrderedExcalidrawElement } from "@excalidraw/excalidraw/element/types";
import { RemoteExcalidrawElement } from "@excalidraw/excalidraw/data/reconcile";


const WS_THROTTLE_INTERVAL = 1_000;
const WS_RESPONSE_TIMEOUT = 7_000;
const WS_PING_INTERVAL = 30_000;
const WS_FULL_SYNC_INTERVAL = 20_000;


enum ExcalidrawCollabEventType {
  INIT = 'collab.init',
  CONNECT = 'collab.connect',
  DISCONNECT = 'collab.disconnect',
  UPDATE = 'collab.update_excalidraw',
  PING = 'ping',
  ERROR = 'error',
};

type ExcalidrawCollabEvent = {
  type: ExcalidrawCollabEventType;
  client_id?: string;
  elements?: readonly ExcalidrawElement[];
  syncall?: boolean;
}


type WebsocketConnectionOptions = {
  path: string;
  onReceiveMessage: (message: ExcalidrawCollabEvent) => void;
  onDisconnect?: () => void;
};

class WebsocketConnection {
  wsUrl: string;
  websocket: WebSocket | null = null;
  pingIntervalId: number | null = null;
  readonly options: WebsocketConnectionOptions;

  constructor(options: WebsocketConnectionOptions) {
    this.options = options;
    const serverUrl = process.env.NODE_ENV === 'development' ?
      'ws://localhost:3000/' :
      `${window.location.protocol === 'http:' ? 'ws' : 'wss'}://${window.location.host}/`;
    this.wsUrl = urlJoin(serverUrl, options.path);
  }

  async connect() {
    return await new Promise<void>((resolve, reject) => {
      if (this.websocket && this.websocket.readyState !== WebSocket.CLOSED) {
        resolve();
        return;
      }

      this.websocket = new WebSocket(this.wsUrl);
      this.websocket.addEventListener('open', () => {
        this.pingIntervalId = window.setInterval(() => this.sendPing(), WS_PING_INTERVAL);
      });
      this.websocket.addEventListener('close', (event: CloseEvent) => {
        this.websocket = null;
        window.clearInterval(this.pingIntervalId ?? undefined);
        this.websocketResponseTimeout.cancel();

        // eslint-disable-next-line no-console
        console.log('Websocket closed', event);

        reject(event);
      });
      this.websocket.addEventListener('message', (event) => {
        // Reset connection loss detection
        this.websocketResponseTimeout.cancel();

        // Handle message
        const msgData = JSON.parse(event.data) as ExcalidrawCollabEvent;
        this.options.onReceiveMessage(msgData);

        if (msgData.type === ExcalidrawCollabEventType.INIT) {
          resolve();
        }
      });
      
    });
  }

  websocketResponseTimeout = throttle(() => {
    // Possible reasons: network outage, browser tab becomes inactive, server crashes
    if (this.websocket && ![WebSocket.CLOSED, WebSocket.CLOSING].includes(this.websocket.readyState as any)) {
      this.websocket?.close(4504, 'Connection loss detection timeout');
    }
  }, WS_RESPONSE_TIMEOUT, { leading: false, trailing: true });

  async disconnect() {
    if ([WebSocket.CLOSED, WebSocket.CLOSING].includes(this.websocket?.readyState as any)) {
      return;
    }

    if (this.websocket?.readyState === WebSocket.OPEN) {
      await new Promise<void>((resolve) => {
        this.websocket?.addEventListener('close', () => resolve(), { once: true });
        this.websocket?.close(1000, 'Disconnect');
      });
    }
  }

  send(msg: ExcalidrawCollabEvent) {
    if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
      return;
    }
    console.log('websocket.send', msg);
    this.websocket?.send(JSON.stringify(msg));
    this.websocketResponseTimeout();
  }

  sendPing() {
    this.send({ 
      type: ExcalidrawCollabEventType.PING,
    });
  }
}


interface CollabProps {
  excalidrawAPI: ExcalidrawImperativeAPI;
  path: string;
  onConnectionChange?: (isConnected: boolean) => void;
};

export class SysreptorCollab extends PureComponent<CollabProps> {
  excalidrawAPI: ExcalidrawImperativeAPI;
  path: string;

  clientId: string | null = null;
  connection: WebsocketConnection | null = null;
  lastUpdateVersion: number = 0;
  lastSyncAllVersion: number = 0;
  broadcastedElementVersions = new Map<string, number>();

  constructor(props: CollabProps) {
    super(props);
    this.excalidrawAPI = props.excalidrawAPI;
    this.path = props.path;
  }

  componentDidMount(): void {
    window.addEventListener('beforeunload', this.onBeforeUnload.bind(this));
    window.addEventListener('unload', this.onUnload.bind(this));
  }

  componentWillUnmount(): void {
    this.connection?.disconnect();
    window.removeEventListener('beforeunload', this.onBeforeUnload);
    window.removeEventListener('unload', this.onUnload);
  }

  private onBeforeUnload() {
    this.syncElements({ syncAll: true });
  }

  private onUnload() {
    this.connection?.disconnect();
  }

  syncElements(options: { elements?: readonly OrderedExcalidrawElement[], syncAll?: boolean }) {
    // sync out only the elements we think we need to to save bandwidth.
    // periodically we'll resync the whole thing to make sure no one diverges
    // due to a dropped message (server goes down etc).
    const elements = (options.elements || this.excalidrawAPI.getSceneElementsIncludingDeleted());
    const version = hashElementsVersion(elements);
    const syncableElements = elements
      .filter(element => isSyncableElement(element) && (
        options?.syncAll ||
        !this.broadcastedElementVersions.has(element.id) ||
        element.version > this.broadcastedElementVersions.get(element.id)!)
      );
    if (syncableElements.length === 0 || version === (options?.syncAll ? this.lastSyncAllVersion : this.lastUpdateVersion)) {
      // Already synced, no new changes
      return;
    }
    
    // Send websocket message
    this.connection?.send({
      type: ExcalidrawCollabEventType.UPDATE,
      elements: syncableElements,
      syncall: options?.syncAll,
    });

    // Update versions
    this.lastUpdateVersion = version;
    for (const element of syncableElements) {
      this.broadcastedElementVersions.set(element.id, element.version);
    }

    if (!options?.syncAll) {
      this.syncAllElementsThrottled();
    } else {
      // Already synced
      this.syncElementsThrottled.cancel();
      this.syncAllElementsThrottled.cancel();
    }
  }

  syncElementsThrottled = throttle((options: { elements?: readonly OrderedExcalidrawElement[] }) => {
    this.syncElements(options);
  }, WS_THROTTLE_INTERVAL, { leading: false, trailing: true });

  syncAllElementsThrottled = throttle(() => {
    this.syncElements({ syncAll: true });
  }, WS_FULL_SYNC_INTERVAL, { leading: false, trailing: true });

  async connect() {
    // Reset state
    this.clientId = null;
    this.lastUpdateVersion = 0;
    this.lastSyncAllVersion = 0;
    this.broadcastedElementVersions.clear();

    const connection = this.connection = new WebsocketConnection({
      path: this.path,
      onReceiveMessage: (msg) => {
        console.log('onReceiveMessage', msg);
        try {
          if (msg.type === ExcalidrawCollabEventType.INIT) {
            this.clientId = msg.client_id!;
            this.handleRemoteSceneUpdate(msg.elements!);
            // Notify connection is established
            this.props.onConnectionChange?.(true);
          } else if (msg.type === ExcalidrawCollabEventType.UPDATE) {
            this.handleRemoteSceneUpdate(msg.elements!);
            if (msg.syncall) {
              this.lastUpdateVersion = hashElementsVersion(msg.elements!);
            }
          } else if (msg.type === ExcalidrawCollabEventType.CONNECT) {
            // Send current scene to new client
            if (this.clientId !== msg.client_id) {
              this.syncElements({ syncAll: true });
            }
          } else if ([ExcalidrawCollabEventType.PING, ExcalidrawCollabEventType.DISCONNECT].includes(msg.type)) {
            // Do nothing
          } else if (msg.type === ExcalidrawCollabEventType.ERROR) {
            // eslint-disable-next-line no-console
            console.error('Received error from websocket:', msg);
          } else {
            throw new Error(`Unknown message type: ${msg.type}`);
          }
        } catch (error) {
          this.handleCollabError(msg, error);
        }
      },
      onDisconnect: () => {
        if (this.connection === connection) {
          this.connection = null;
          this.clientId = null;
          this.lastUpdateVersion = 0;
          this.lastSyncAllVersion = 0;
          this.broadcastedElementVersions.clear();
          this.syncAllElementsThrottled.clear();
          // Notify connection is lost
          this.props.onConnectionChange?.(false);
        }
      },
    });
    return await connection.connect();
  }

  private handleRemoteSceneUpdate(remoteElements: readonly ExcalidrawElement[]) {
    const reconciledElements = reconcileElements(
      this.excalidrawAPI.getSceneElementsIncludingDeleted(),
      restoreElements(remoteElements, null) as RemoteExcalidrawElement[],
      this.excalidrawAPI.getAppState(),
    );
    this.lastUpdateVersion = hashElementsVersion(reconciledElements);
    this.excalidrawAPI.updateScene({
      elements: reconciledElements,
      captureUpdate: CaptureUpdateAction.NEVER,
    });
  }

  private handleCollabError(event: any, error: any) {
    console.error('Error while processing collab event:', { 
      error, 
      event, 
      version: this.lastUpdateVersion,
    });
    if (this.connection) {
      this.connection.disconnect();
    }
  }

  render() {
    return (<div></div>);
  }
}


function isSyncableElement(element: OrderedExcalidrawElement): boolean {
  if (element.isDeleted) {
    if (element.updated > Date.now() - 24 * 60 * 60 * 1000) {
      return true;
    }
    return false;
  }
  return !isInvisiblySmallElement(element);
}
