import { LibraryPersistedData } from "@excalidraw/excalidraw/data/library";
import { MaybePromise } from "@excalidraw/excalidraw/utility-types";
import { createStore, get, set } from "idb-keyval";


export class LibraryIndexedDBAdapter {
  /** library data store key */
  private static key = "libraryData";

  private static store = createStore(
    `excalidraw-library-db`,
    `excalidraw-library-store`,
  );

  static async load() {
    const IDBData = await get<LibraryPersistedData>(
      LibraryIndexedDBAdapter.key,
      LibraryIndexedDBAdapter.store,
    );

    return IDBData || null;
  }

  static save(data: LibraryPersistedData): MaybePromise<void> {
    return set(
      LibraryIndexedDBAdapter.key,
      data,
      LibraryIndexedDBAdapter.store,
    );
  }
}