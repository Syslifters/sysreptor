import { groupBy, sortBy } from "lodash-es";
import type { NoteBase } from "#imports";

export type NoteGroup<T extends NoteBase> = {
  note: T;
  children: NoteGroup<T>;
}[];


export function groupNotes<T extends NoteBase>(noteList: T[], options?: { parentNoteId: string|null}): NoteGroup<T> {
  const groups = groupBy(noteList, 'parent');

  function collectChildren(parentId: string|null): NoteGroup<T> {
    return sortBy(groups[parentId as any] || [], 'order')
      .map(note => ({ note, children: collectChildren(note.id) }));
  }
  return collectChildren(options?.parentNoteId || null);
}

export function flattenNotes<T extends NoteBase>(noteGroups: NoteGroup<T>): T[] {
  return noteGroups.reduce((acc: T[], group) => {
    acc.push(group.note);
    return acc.concat(flattenNotes(group.children));
  }, []);
}

export function sortNotes<T extends NoteBase>(noteGroups: NoteGroup<T>, commitNote: (n: T) => void) {
  function setParentAndOrder(children: NoteGroup<T>, parentId: string|null) {
    for (let i = 0; i < children.length; i++) {
      const note = {
        ...children[i]!.note,
        parent: parentId,
        order: i + 1
      };
      commitNote(note);
      setParentAndOrder(children[i]!.children, note.id);
    }
  }
  setParentAndOrder(noteGroups, null);
}
