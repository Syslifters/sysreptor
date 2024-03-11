import groupBy from "lodash/groupBy";
import sortBy from "lodash/sortBy";
import pick from "lodash/pick";
import type { UserNote, NoteBase } from "~/utils/types";

export type NoteGroup<T extends NoteBase> = {
  note: T;
  children: NoteGroup<T>;
}[];

export function groupNotes<T extends NoteBase>(noteList: T[]): NoteGroup<T> {
  const groups = groupBy(noteList, 'parent');

  function collectChildren(parentId: string|null): NoteGroup<T> {
    return sortBy(groups[parentId as any] || [], 'order')
      .map(note => ({ note, children: collectChildren(note.id) }));
  }
  return collectChildren(null);
}

export function sortNotes<T extends NoteBase>(noteGroups: NoteGroup<T>, commitNote: (n: T) => void) {
  function setParentAndOrder(children: NoteGroup<T>, parentId: string|null) {
    for (let i = 0; i < children.length; i++) {
      const note = {
        ...children[i].note,
        parent: parentId,
        order: i + 1
      };
      commitNote(note);
      setParentAndOrder(children[i].children, note.id);
    }
  }
  setParentAndOrder(noteGroups, null);
}

export const useUserNotesStore = defineStore('usernotes', {
  state() {
    return {
      notesCollabState: makeCollabStoreState({
        websocketPath: '/ws/pentestusers/self/notes/',
        initialData: { notes: {} as {[key: string]: UserNote} },
        handleAdditionalWebSocketMessages: (msgData: any) => {
          const collabState = (this as any).notesCollabState;
          if (msgData.type === 'collab.sort' && msgData.path === 'notes') {
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
      return Object.values(this.notesCollabState.data.notes);
    },
    noteGroups(): NoteGroup<UserNote> {
      return groupNotes(this.notes);
    },
  },
  actions: {
    clear() {
      this.notesCollabState = [];
    },
    async createNote(note: UserNote) {
      note = await $fetch<UserNote>(`/api/v1/pentestusers/self/notes/`, {
        method: 'POST',
        body: note
      });
      this.notesCollabState.data.notes[note.id] = note;
      return note;
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
    async fetchNotes() {
      const notes = await $fetch<UserNote[]>('/api/v1/pentestusers/self/notes/', { method: 'GET' });
      this.notesCollabState.data.notes = Object.fromEntries(notes.map(n => [n.id, n]));
      return this.notes;
    },
    useNotesCollab() {
      const collabState = this.notesCollabState;
      const collab = useCollab(collabState);

      const hasEditPermissions = computed(() => true);
      return {
        ...collab,
        hasEditPermissions,
        readonly: computed(() => !hasEditPermissions.value || collabState.connectionState !== CollabConnectionState.OPEN),
      }
    }
  }
})
