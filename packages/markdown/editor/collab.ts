/*
This file is based on @codemirror/collab.

MIT License

Copyright (C) 2018-2021 by Marijn Haverbeke <marijn@haverbeke.berlin> and others

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
*/

import { Facet, ChangeSet, StateField, Annotation, EditorState, StateEffect,
  Transaction, combineConfig, type Extension } from "@codemirror/state"

/// An update is a set of changes and effects.
export interface Update {
  /// The changes made by this update.
  changes: ChangeSet;
  /// The effects in this update. There'll only ever be effects here
  /// when you configure your collab extension with a
  /// [`sharedEffects`](#collab.collab^config.sharedEffects) option.
  effects?: readonly StateEffect<any>[];
  /// The [ID](#collab.collab^config.clientID) of the client who
  /// created this update.
  clientID: string;
  /// The document version this update is based on.
  version: number;
}

class LocalUpdate implements Update {
  constructor(
    readonly origin: Transaction,
    readonly changes: ChangeSet,
    readonly effects: readonly StateEffect<any>[],
    readonly clientID: string,
    readonly version: number = 0,
  ) {}
}

class CollabState {
  constructor(
    // The version up to which changes have been confirmed.
    readonly version: number,
    // The local updates that havent been successfully sent to the
    // server yet.
    readonly unconfirmed: readonly LocalUpdate[],
  ) {}
}

type CollabConfig = {
  /// The starting document version. Defaults to 0.
  startVersion?: number,
  /// This client's identifying [ID](#collab.getClientID). Will be a
  /// randomly generated string if not provided.
  clientID?: string,
  /// It is possible to share information other than document changes
  /// through this extension. If you provide this option, your
  /// function will be called on each transaction, and the effects it
  /// returns will be sent to the server, much like changes are. Such
  /// effects are automatically remapped when conflicting remote
  /// changes come in.
  sharedEffects?: (tr: Transaction) => readonly StateEffect<any>[]
}

const collabConfig = Facet.define<CollabConfig & {generatedID: string}, Required<CollabConfig>>({
  combine(configs) {
    let combined = combineConfig(configs, {startVersion: 0, clientID: null as any, sharedEffects: () => []}, {
      generatedID: a => a
    })
    if (combined.clientID == null) combined.clientID = (configs.length && configs[0].generatedID) || ""
    return combined
  }
})

const collabReceive = Annotation.define<CollabState>()

const collabField = StateField.define({
  create(state) {
    return new CollabState(state.facet(collabConfig).startVersion, [])
  },

  update(collab: CollabState, tr: Transaction) {
    let isSync = tr.annotation(collabReceive)
    if (isSync) return isSync
    let {sharedEffects, clientID} = tr.startState.facet(collabConfig)
    let effects = sharedEffects(tr)
    if (effects.length || !tr.changes.empty)
      return new CollabState(collab.version, collab.unconfirmed.concat(new LocalUpdate(tr, tr.changes, effects, clientID)))
    return collab
  }
})

/// Create an instance of the collaborative editing plugin.
export function collab(config: CollabConfig = {}): Extension {
  return [collabField, collabConfig.of({generatedID: Math.floor(Math.random() * 1e9).toString(36), ...config})]
}

/// Create a transaction that represents a set of new updates received
/// from the authority. Applying this transaction moves the state
/// forward to adjust to the authority's view of the document.
export function receiveUpdates(state: EditorState, updates: readonly Update[]) {
  let {unconfirmed} = state.field(collabField)
  let {clientID} = state.facet(collabConfig)

  let effects: readonly StateEffect<any>[] = [], changes: ChangeSet|null = null

  let version = 0;
  let own = 0
  for (let update of updates) {
    let ours = own < unconfirmed.length ? unconfirmed[own] : null
    if (ours && ours.clientID == update.clientID) {
      if (changes) changes = changes.map(ours.changes, true)
      effects = StateEffect.mapEffects(effects, update.changes)
      own++
    } else {
      effects = StateEffect.mapEffects(effects, update.changes)
      if (update.effects) effects = effects.concat(update.effects)
      changes = changes ? changes.compose(update.changes) : update.changes
    }
    if (update.version! > version) {
      version = update.version!;
    }
  }

  if (own) { 
    unconfirmed = unconfirmed.slice(own);
  }
  if (unconfirmed.length > 0) {
    if (changes) {
        unconfirmed = unconfirmed.map(update => {
          let updateChanges = update.changes.map(changes!)
          changes = changes!.map(update.changes, true)
          return new LocalUpdate(update.origin, updateChanges, StateEffect.mapEffects(update.effects, changes!), clientID, version)
        });
      }
    if (effects.length > 0) {
      let composed = unconfirmed.reduce((ch, u) => ch.compose(u.changes),
                                        ChangeSet.empty(unconfirmed[0].changes.length))
      effects = StateEffect.mapEffects(effects, composed)
    }
  }

  if (!changes) {
    return state.update({annotations: [
      collabReceive.of(new CollabState(version, unconfirmed))
    ]});
  } else {
    return state.update({
      changes: changes,
      effects,
      annotations: [
        Transaction.addToHistory.of(false),
        Transaction.remote.of(true),
        collabReceive.of(new CollabState(version, unconfirmed))
      ],
      filter: false
    })
  }
}

/// Returns the set of locally made updates that still have to be sent
/// to the authority. The returned objects will also have an `origin`
/// property that points at the transaction that created them. This
/// may be useful if you want to send along metadata like timestamps.
/// (But note that the updates may have been mapped in the meantime,
/// whereas the transaction is just the original transaction that
/// created them.)
export function sendableUpdates(state: EditorState): readonly Update[] {
  let cf = state.field(collabField);
  return cf.unconfirmed.map(u => ({
    clientID: u.clientID,
    version: cf.version,
    changes: u.changes.toJSON(),
  }))
}
