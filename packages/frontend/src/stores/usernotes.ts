import { groupBy, sortBy, pick } from "lodash-es";
import type { UserNote, NoteBase } from "#imports";

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

export const useUserNotesStore = defineStore('usernotes', {
  state() {
    return {
      notesCollabState: makeCollabStoreState({
        apiPath: '/api/ws/pentestusers/self/notes/',
        initialData: { notes: {} as Record<string, UserNote> },
        initialPath: 'notes',
        handleAdditionalWebSocketMessages: (msgData: any, collabState) => {
          if (msgData.type === CollabEventType.SORT && msgData.path === 'notes') {
            for (const note of Object.values(collabState.data.notes) as UserNote[]) {
              const no = msgData.sort.find((n: UserNote) => n.id === note.id);
              note.parent = no?.parent || null;
              note.order = no?.order || 0;
            }
            return true;
          } else {
            return false;
          }
        }
      }),
    };
  },
  getters: {
    notes(): UserNote[] {
      return Object.values(this.notesCollabState?.data?.notes || {});
    },
    noteGroups(): NoteGroup<UserNote> {
      return groupNotes(this.notes);
    },
  },
  actions: {
    async createNote(note: Partial<UserNote>) {
      const newNote = await $fetch<UserNote>(`/api/v1/pentestusers/self/notes/`, {
        method: 'POST',
        body: note
      });
      this.notesCollabState.data.notes[newNote.id] = newNote;
      return newNote;
    },
    async deleteNote(note: UserNote) {
      await $fetch(`/api/v1/pentestusers/self/notes/${note.id}/`, {
        method: 'DELETE'
      });
      delete this.notesCollabState.data.notes[note.id];
    },
    async sortNotes(noteGroups: NoteGroup<UserNote>) {
      const notes = [] as UserNote[];
      sortNotes(noteGroups, (n) => {
        notes.push(n);
      });
      this.notesCollabState.data.notes = Object.fromEntries(notes.map(n => [n.id, n]));
      await $fetch<{id: string; parent: string|null; order: number}[]>(`/api/v1/pentestusers/self/notes/sort/`, {
        method: 'POST',
        body: notes.map(n => pick(n, ['id', 'parent', 'order']))
      });
    },
    useNotesCollab(options?: { noteId?: string }) {
      const collabState = this.notesCollabState;
      const collab = useCollab(collabState as CollabStoreState<{ notes: Record<string, UserNote> }>);

      return {
        ...collab,
        collabProps: computed<CollabPropType>((oldValue) => collabSubpath(
          collab.collabProps.value, 
          options?.noteId ? `notes.${options.noteId}` : null, 
          oldValue
        )),
      }
    },
  }
})
