import { describe, test, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { v4 as uuid4 } from 'uuid'
import { cloneDeep } from 'lodash-es'
import { CollabEventType, type CollabEvent, type Comment, type User } from '#imports';
import { ChangeSet, EditorSelection } from '@sysreptor/markdown/editor';


async function createCollab(options?: { collabInitEvent?: Partial<CollabEvent> }) {
  vi.useFakeTimers();
  setActivePinia(createPinia());

  const storeState = reactive(makeCollabStoreState({
    apiPath: '/api/ws/test/',
    initialData: {},
  })) as CollabStoreState<any>;
  const collab = useCollab(storeState);

  const connection = {
    type: CollabConnectionType.WEBSOCKET,
    connectionState: CollabConnectionState.CONNECTING,
    connectionConfig: {
      throttleInterval: 1000,
    },
    connect: vi.fn(),
    disconnect: vi.fn(),
    send: vi.fn(),
    receive: collab.onReceiveMessage,
  }
  await collab.connectTo(connection);

  const commentIdText = uuid4();
  const commentIdList = uuid4();
  const collabInitEvent = {
    type: CollabEventType.INIT,
    version: 1,
    client_id: 'self',
    path: null,
    permissions: {
      read: true,
      write: true,
    },
    data: {
      field_text: 'ABCD',
      field_key: 'value',
      field_list: ['a', 'b', 'c'],
      comments: {
        [commentIdText]: {
          id: commentIdText,
          text: 'comment on field_text',
          path: 'field_text',
          text_range: { from: 1, to: 2 }, // 'BC'
        },
        [commentIdList]: {
          id: commentIdList,
          text: 'comment on field_list[0]',
          path: 'field_list.[0]',
          text_range: { from: 0, to: 1 }, // 'a'
        }
      },
    },
    clients: [
      {
        client_id: 'self',
        client_color: 'red',
        user: { id: uuid4(), username: 'user', name: 'User Name' } as unknown as User,
      },
      {
        client_id: 'other',
        client_color: 'blue',
        user: { id: uuid4(), username: 'other', name: 'Other User' } as unknown as User,
      }
    ],
    ...(options?.collabInitEvent || {})
  }
  connection.receive(cloneDeep(collabInitEvent));

  collab.storeState.awareness.other['other'] = {
    path: 'field_text',
    selection: EditorSelection.create([EditorSelection.range(1, 2)]),
  }

  // Reset mocks
  await vi.runOnlyPendingTimersAsync();
  vi.clearAllMocks();

  return {
    collab,
    connection: connection as typeof connection & CollabConnectionInfo,
    collabInitEvent,
  }
}

function createReceivedEvent(event: Partial<CollabEvent>): CollabEvent {
  const defaultData = {
    version: 2,
    client_id: 'other',
  } as Partial<CollabEvent>;

  if (event.type === CollabEventType.UPDATE_KEY) {
    Object.assign(defaultData, {
      path: 'field_key',
      value: 'changed value',
    });
  } else if (event.type === CollabEventType.UPDATE_TEXT) {
    Object.assign(defaultData, {
      path: 'field_text',
      updates: [{ changes: [0, [0, 'a']]}],
    });
  }

  return {
    ...defaultData,
    ...event,
  } as CollabEvent;
}

function expectEventsSentInConnection(connection: any, events: Partial<CollabEvent>[]) {
  vi.runOnlyPendingTimers();
  expect(connection.send).toHaveBeenCalledTimes(1);
  const sendArgs = connection.send.mock.calls[0]![0]! as CollabEvent[];
  expect(sendArgs.length).toBe(events.length);
  for (let i = 0; i < events.length; i++) {
    expect(sendArgs[i]).toMatchObject(events[i]!);
  }
}


describe('connection', () => {
  let { collab, connection }: Awaited<ReturnType<typeof createCollab>> = {} as any;
  beforeEach(async () => {
    const res = await createCollab(); 
    collab = res.collab;
    connection = res.connection;
  })

  test('disconnect gracefully', async () => {
    await collab.disconnect();
    expect(connection.disconnect).toHaveBeenCalled();
  });

  test('disconnect on error', async () => {
    connection.receive(createReceivedEvent({
      type: CollabEventType.UPDATE_TEXT,
      path: 'field_text',
      updates: [{ changes: [10, [0, 'a']]}],  // Invalid update
    }));
    expect(connection.disconnect).toHaveBeenCalled();
    expect(connection.connectionError).toBeTruthy();
  });

  test('send after disconnect', async () => {
    await collab.disconnect();
    connection.send.mockClear();
    collab.onCollabEvent({type: CollabEventType.UPDATE_KEY, path: collab.storeState.apiPath + 'field_key', value: 'value'});
    await vi.runOnlyPendingTimersAsync();
    expect(connection.send).not.toHaveBeenCalled();
  });

  test('flush send on disconnect', async () => {
    collab.onCollabEvent({type: CollabEventType.UPDATE_KEY, path: collab.storeState.apiPath + 'field_key', value: 'value'});
    expect(connection.send).not.toHaveBeenCalled();
    await collab.disconnect();
    expect(connection.send).toHaveBeenCalled();
  });

  test('send throttling', async () => {
    collab.onCollabEvent({type: CollabEventType.UPDATE_KEY, path: collab.storeState.apiPath + 'field_key', value: 'value'});
    expect(connection.send).not.toHaveBeenCalled();
    await vi.runOnlyPendingTimersAsync();
    expect(connection.send).toHaveBeenCalled();
  });

  test('send immediate', async () => {
    collab.onCollabEvent({type: CollabEventType.CREATE, path: collab.storeState.apiPath + 'field_new', value: 'value'});
    expect(connection.send).toHaveBeenCalled();
  });

  test('ignore events for other connections', async () => {
    collab.onCollabEvent({type: CollabEventType.CREATE, path: 'not_for' + collab.storeState.apiPath + 'field_new', value: 'value'});
    expect(connection.send).not.toHaveBeenCalled();
  })
});


describe('readonly connection', () => {
  let { connection, collab, collabInitEvent }: Awaited<ReturnType<typeof createCollab>> = {} as any;
  beforeEach(async () => {
    const res = await createCollab({
      collabInitEvent: {
        permissions: {
          read: true,
          write: false,
        }
      }
    });
    collab = res.collab;
    connection = res.connection;
    collabInitEvent = res.collabInitEvent;
  });

  test('no events sent', async () => {
    collab.onCollabEvent({ type: CollabEventType.AWARENESS, path: collab.storeState.apiPath + 'field_text'});
    collab.onCollabEvent({ type: CollabEventType.UPDATE_KEY, path: collab.storeState.apiPath + 'field_key', value: 'x' });
    collab.onCollabEvent({ type: CollabEventType.DELETE, path: collab.storeState.apiPath + 'field_list[0]' });
    collab.onCollabEvent({ type: CollabEventType.CREATE, path: collab.storeState.apiPath + 'field_list', value: 'new'});
    collab.onCollabEvent({ 
      type: CollabEventType.UPDATE_TEXT, 
      path: collab.storeState.apiPath + 'field_text', 
      updates: [{changes: ChangeSet.fromJSON([4, [0, 'E']])}]
    });
    await vi.runOnlyPendingTimersAsync();
    expect(connection.send).not.toHaveBeenCalled();
    expect(collab.storeState.data).toEqual(collabInitEvent.data);
    expect(collab.storeState.awareness.self).toEqual({ path: '' });
  });
});


describe('send and receive', () => {
  let { collab, connection, collabInitEvent }: Awaited<ReturnType<typeof createCollab>> = {} as any;
  beforeEach(async () => {
    const res = await createCollab();
    collab = res.collab;
    connection = res.connection;
    collabInitEvent = res.collabInitEvent;
  });

  function expectEventsSent(...events: Partial<CollabEvent>[]) {
    expectEventsSentInConnection(connection, events);
  }

  test('version updated', () => {
    const newVersion = 1234;
    connection.receive(createReceivedEvent({type: CollabEventType.UPDATE_KEY, version: newVersion}));
    expect(collab.storeState.version).toBe(newVersion);
  });

  test('collab.update_key', () => {
    const newValue = 'changed value';
    connection.receive(createReceivedEvent({type: CollabEventType.UPDATE_KEY, path: 'field_key', value: newValue}));
    expect(collab.storeState.data.field_key).toBe(newValue);
  });

  test('collab.update_key clear pending events of child fields', async () => {
    const newValue = ['c', 'b', 'a'];
    collab.onCollabEvent({
      type: CollabEventType.UPDATE_KEY,
      path: collab.storeState.apiPath + 'field_list.[0]',
      value: 'x',
    });
    collab.onCollabEvent({
      type: CollabEventType.UPDATE_TEXT,
      path: collab.storeState.apiPath + 'field_list.[1]',
      updates: [{ changes: ChangeSet.fromJSON([1, [0, 'y']]) }],
    });
    connection.receive(createReceivedEvent({type: CollabEventType.UPDATE_KEY, path: 'field_list', value: newValue}));
    await vi.runOnlyPendingTimersAsync();
    expect(collab.storeState.data.field_list).toEqual(newValue);
    expect(connection.send).not.toHaveBeenCalled();
  });

  test('collab.create', () => {
    const newValue = 'new value';
    connection.receive(createReceivedEvent({type: CollabEventType.CREATE, path: 'field_new', value: newValue}));
    expect(collab.storeState.data.field_new).toBe(newValue);
  });

  test('collab.delete', () => {
    connection.receive(createReceivedEvent({type: CollabEventType.DELETE, path: 'field_text'}));
    expect(collab.storeState.data.field_text).toBeUndefined();
  });

  test('collab.create list', () => {
    const newValue = 'new value';
    connection.receive(createReceivedEvent({type: CollabEventType.CREATE, path: 'field_list.[3]', value: newValue}));
    expect(collab.storeState.data.field_list[3]).toBe(newValue);
    expect(collab.storeState.data.field_list.length).toBe(4);
  });

  test('collab.delete list', () => {
    connection.receive(createReceivedEvent({type: CollabEventType.DELETE, path: 'field_list.[1]'}));
    const newList = collabInitEvent.data.field_list;
    newList.splice(1, 1);
    expect(collab.storeState.data.field_list.length).toBe(newList.length);
    expect(collab.storeState.data.field_list).toEqual(newList);
  });

  test('collab.connect', () => {
    connection.receive(createReceivedEvent({
      type: CollabEventType.CONNECT,
      client_id: 'other2',
      client: {
        client_id: 'other2',
        client_color: 'green',
        user: { id: uuid4(), username: 'other2', name: 'Other User 2' } as unknown as User,
      },
    }));
    expect(collab.storeState.awareness.clients.at(-1)?.client_id).toBe('other2');
  });

  test('collab.disconnect', () => {
    connection.receive(createReceivedEvent({type: CollabEventType.DISCONNECT, client_id: 'other'}));
    expect(collab.storeState.awareness.clients.length).toBe(1);
  })

  test('collab.awareness', () => {
    const selection = EditorSelection.create([EditorSelection.range(0, 1)]).toJSON();
    connection.receive(createReceivedEvent({
      type: CollabEventType.AWARENESS,
      client_id: 'other',
      path: 'field_text',
      selection,
    }));
    const updatedAwareness = collab.storeState.awareness.other['other']!;
    expect(updatedAwareness.path).toBe('field_text');
    expect(updatedAwareness.selection?.toJSON()).toEqual(selection);
  });

  test('multiple collab.update_key: only last one sent', () => {
    collab.onCollabEvent({type: CollabEventType.UPDATE_KEY, path: collab.storeState.apiPath + 'field_key', value: 'value1'});
    collab.onCollabEvent({type: CollabEventType.UPDATE_KEY, path: collab.storeState.apiPath + 'field_key', value: 'value2'});
    expectEventsSent({type: CollabEventType.UPDATE_KEY, path: 'field_key', value: 'value2'});
  });

  test('multiple collab.update_text: combined', async () => {
    const updates1 = [{changes: ChangeSet.fromJSON([4, [0, 'E']])}];
    const updates2 = [{changes: ChangeSet.fromJSON([5, [0, 'F']])}]
    collab.onCollabEvent({type: CollabEventType.UPDATE_TEXT, path: collab.storeState.apiPath + 'field_text', updates: updates1});
    collab.onCollabEvent({type: CollabEventType.UPDATE_TEXT, path: collab.storeState.apiPath + 'field_text', updates: updates2});
    expectEventsSent({type: CollabEventType.UPDATE_TEXT, path: 'field_text', updates: updates1.concat(updates2).map(u => ({changes: u.changes.toJSON()}))});
  });
});


describe('collab.awareness', () => {
  let { collab, connection }: Awaited<ReturnType<typeof createCollab>> = {} as any;
  beforeEach(async () => {
    const res = await createCollab();
    collab = res.collab;
    connection = res.connection;
  });

  function expectEventsSent(...events: Partial<CollabEvent>[]) {
    expectEventsSentInConnection(connection, events);
  }

  test('multiple collab.awareness events: only last one sent', () => {
    collab.onCollabEvent({type: CollabEventType.AWARENESS, path: collab.storeState.apiPath + 'field_key'});
    const selection = EditorSelection.create([EditorSelection.cursor(1)])
    collab.onCollabEvent({type: CollabEventType.AWARENESS, path: collab.storeState.apiPath + 'field_text', selection});
    expectEventsSent({type: CollabEventType.AWARENESS, path: 'field_text', selection: selection.toJSON()});
  });

  test('collab.update_text with selection: collab.awareness not sent', () => {
    collab.onCollabEvent({type: CollabEventType.AWARENESS, path: collab.storeState.apiPath + 'field_text', selection: EditorSelection.create([EditorSelection.cursor(0)])});
    collab.onCollabEvent({
      type: CollabEventType.UPDATE_TEXT,
      path: collab.storeState.apiPath + 'field_text',
      updates: [{ changes: ChangeSet.fromJSON([4, [0, 'E']]) }],
    });
    const selection = EditorSelection.create([EditorSelection.range(0, 2)]);
    collab.onCollabEvent({type: CollabEventType.AWARENESS, path: collab.storeState.apiPath + 'field_text', selection})
    expectEventsSent({type: CollabEventType.UPDATE_TEXT, path: 'field_text', selection: selection.toJSON()});
  });

  test('collab.update_text with selection, then other field focussed: collab.awareness sent, update_text.selection=undefined', () => {
    collab.onCollabEvent({
      type: CollabEventType.UPDATE_TEXT,
      path: collab.storeState.apiPath + 'field_text',
      updates: [{ changes: ChangeSet.fromJSON([4, [0, 'E']]) }],
    });
    collab.onCollabEvent({type: CollabEventType.AWARENESS, path: collab.storeState.apiPath + 'field_text', Selection: EditorSelection.create([EditorSelection.cursor(1)])});
    collab.onCollabEvent({type: CollabEventType.AWARENESS, path: collab.storeState.apiPath + 'field_key'});
    expectEventsSent(
      {type: CollabEventType.UPDATE_TEXT, path: 'field_text', selection: undefined},
      {type: CollabEventType.AWARENESS, path: 'field_key'},
    );
  })

  test('collab.update_key with update_awareness=True: collab.awareness not sent', () => {
    collab.onCollabEvent({type: CollabEventType.AWARENESS, path: collab.storeState.apiPath + 'field_text'});
    collab.onCollabEvent({
      type: CollabEventType.UPDATE_KEY,
      path: collab.storeState.apiPath + 'field_key',
      value: 'value',
      updateAwareness: true,
    });
    expectEventsSent({type: CollabEventType.UPDATE_KEY, path: 'field_key', update_awareness: true});
  });

  test('collab.update_key with update_awareness=False: collab.awareness sent', () => {
    collab.onCollabEvent({type: CollabEventType.AWARENESS, path: collab.storeState.apiPath + 'field_text'});
    collab.onCollabEvent({
      type: CollabEventType.UPDATE_KEY,
      path: collab.storeState.apiPath + 'field_key',
      value: 'value',
      updateAwareness: false,
    });
    expectEventsSent(
      {type: CollabEventType.UPDATE_KEY, path: 'field_key', update_awareness: false },
      {type: CollabEventType.AWARENESS, path: 'field_text'},
    );
  });

  test('collab.update_key with update_awareness=True, other field focussed: collab.awareness sent', () => {
    collab.onCollabEvent({
      type: CollabEventType.UPDATE_KEY,
      path: collab.storeState.apiPath + 'field_key',
      value: 'value',
      updateAwareness: true,
    });
    collab.onCollabEvent({type: CollabEventType.AWARENESS, path: collab.storeState.apiPath + 'field_text'});
    expectEventsSent(
      {type: CollabEventType.UPDATE_KEY, path: 'field_key', update_awareness: false},
      {type: CollabEventType.AWARENESS, path: 'field_text'},
    );
  });
});


describe('collab.update_text', () => {
  let { collab, connection, collabInitEvent }: Awaited<ReturnType<typeof createCollab>> = {} as any;
  beforeEach(async () => {
    const res = await createCollab();
    collab = res.collab;
    connection = res.connection;
    collabInitEvent = res.collabInitEvent;
  });

  test('send', () => {
    collab.onCollabEvent({
      type: CollabEventType.UPDATE_TEXT,
      path: collab.storeState.apiPath + 'field_text',
      updates: [{ changes: ChangeSet.fromJSON([4, [0, 'E']]) }],
    });
    const selection = EditorSelection.create([EditorSelection.range(0, 1)]);
    collab.onCollabEvent({
      type: CollabEventType.UPDATE_TEXT,
      path: collab.storeState.apiPath + 'field_text',
      updates: [{ changes: ChangeSet.fromJSON([0, [0, '0'], 5]) }],
    });
    collab.onCollabEvent({type: CollabEventType.AWARENESS, path: collab.storeState.apiPath + 'field_text', selection});

    // Text updated
    expect(collab.storeState.data.field_text).toBe('0ABCDE');

    // Awareness of self updated
    expect(collab.storeState.awareness.self).toEqual({
      path: 'field_text',
      selection,
    });

    // Selection position of other users updated
    expect(collab.storeState.awareness.other['other']).toEqual({
      path: 'field_text',
      selection: EditorSelection.create([EditorSelection.range(2, 3)]),
    });

    // Comment positions updated
    const commentId = Object.values(collabInitEvent.data.comments as Record<string, Partial<Comment>>).find(c => c.path === 'field_text')!.id!;
    expect(collab.storeState.data.comments[commentId].text_range).toEqual(EditorSelection.range(2, 3));
  });

  test('receive: no unconfirmedTextUpdates', () => {
    collab.storeState.awareness.self = {
      path: 'field_text',
      selection: EditorSelection.create([EditorSelection.range(1, 2)]),
    }

    const selection = EditorSelection.create([EditorSelection.range(0, 1)]);
    const commentId = Object.values(collabInitEvent.data.comments as Record<string, Partial<Comment>>).find(c => c.path === 'field_text')!.id;
    connection.receive(createReceivedEvent({
      type: CollabEventType.UPDATE_TEXT,
      client_id: 'other',
      path: 'field_text',
      updates: [{ changes: [0, [0, '0'], 4] }],
      selection: selection.toJSON(),
      comments: [{ id: commentId, path: 'field_text', text_range: { from: 2, to: 3 }}],
    }));

    // Text updated
    expect(collab.storeState.data.field_text).toBe('0ABCD');

    // Awareness of other user updated
    expect(collab.storeState.awareness.other['other']).toEqual({
      path: 'field_text',
      selection,
    });

    // Selection position of self updated
    expect(collab.storeState.awareness.self).toEqual({
      path: 'field_text',
      selection: EditorSelection.create([EditorSelection.range(2, 3)])
    });

    // Comment positions updated
    const commentActual = Object.values(collab.storeState.data.comments as Record<string, Partial<Comment>>).find(c => c.id === commentId)!;
    expect(commentActual.path).toBe('field_text');
    expect(commentActual.text_range).toEqual(EditorSelection.range(2, 3));
  });

  test('receive: rebase onto unconfirmedTextUpdates', () => {
    const selection = EditorSelection.create([EditorSelection.range(0, 1)]);
    collab.onCollabEvent({
      type: CollabEventType.UPDATE_TEXT,
      path: collab.storeState.apiPath + 'field_text',
      updates: [{ changes: ChangeSet.fromJSON([0, [0, '0'], 4]) }],
    });
    collab.onCollabEvent({type: CollabEventType.AWARENESS, path: collab.storeState.apiPath + 'field_text', selection});
    const commentId = Object.values(collabInitEvent.data.comments as Record<string, Partial<Comment>>).find(c => c.path === 'field_text')!.id!;
    connection.receive(createReceivedEvent({
      type: CollabEventType.UPDATE_TEXT,
      client_id: 'other',
      path: 'field_text',
      updates: [{ changes: [4, [0, 'E']] }],
      selection: EditorSelection.create([EditorSelection.range(1, 2)]).toJSON(),
    }));

    // Text updated
    expect(collab.storeState.data.field_text).toBe('0ABCDE');

    // Awareness of self updated
    expect(collab.storeState.awareness.self).toEqual({
      path: 'field_text',
      selection,
    });

    // Selection position of other users updated: rebased onto unconfirmedTextUpdates
    expect(collab.storeState.awareness.other['other']).toEqual({
      path: 'field_text',
      selection: EditorSelection.create([EditorSelection.range(2, 3)]),
    });

    // Comment positions updated: rebased onto unconfirmedTextUpdates
    const commentActual = collab.storeState.data.comments[commentId];
    expect(commentActual.path).toBe('field_text');
    expect(commentActual.text_range).toEqual(EditorSelection.range(2, 3));

    // Rebase collab.awareness
    connection.receive({
      type: CollabEventType.AWARENESS,
      client_id: 'other',
      path: 'field_text',
      selection: EditorSelection.create([EditorSelection.cursor(1)]).toJSON(),
    });
    expect(collab.storeState.awareness.other['other']).toEqual({
      path: 'field_text',
      selection: EditorSelection.create([EditorSelection.cursor(2)]),
    });
  });

  test('receive: confirm unconfirmedTextUpdates', () => {
    const updates = [{ changes: ChangeSet.fromJSON([4, [0, 'E']]) }];
    collab.onCollabEvent({
      type: CollabEventType.UPDATE_TEXT,
      path: collab.storeState.apiPath + 'field_text',
      updates,
    });
    expect(collab.storeState.perPathState.get('field_text')!.unconfirmedTextUpdates).toEqual(updates);

    connection.receive({
      type: CollabEventType.UPDATE_TEXT,
      client_id: 'self',
      path: 'field_text',
      updates: updates.map(u => ({ changes: u.changes.toJSON() })),
    });
    expect(collab.storeState.perPathState.get('field_text')!.unconfirmedTextUpdates).toEqual([]);
  });
});

