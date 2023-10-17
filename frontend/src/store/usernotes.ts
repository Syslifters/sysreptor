import groupBy from "lodash/groupBy";
import sortBy from "lodash/sortBy";
import pick from "lodash/pick";
import { UserNote } from "~/utils/types";

export type NoteGroup<T extends UserNote> = {
  note: T;
  children: NoteGroup<T>;
}[];

export function groupNotes<T extends UserNote>(noteList: T[]): NoteGroup<T> {
  const groups = groupBy(noteList, 'parent');

  function collectChildren(parentId: string|null): NoteGroup<T> {
    return sortBy(groups[parentId as any] || [], 'order')
      .map(note => ({ note, children: collectChildren(note.id) }));
  }
  return collectChildren(null);
}

export function sortNotes<T extends UserNote>(noteGroups: NoteGroup<T>, commitNote: (n: T) => void) {
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
  state: () => ({
    notes: [] as UserNote[],
  }),
  getters: {
    noteGroups() {
      return groupNotes(this.notes);
    },
  },
  actions: {
    clear() {
      this.notes = [];
    },
    async fetchNotes() {
      this.notes = await $fetch<UserNote[]>('/api/v1/pentestusers/self/notes/', { method: 'GET' });
      return this.notes;
    },
    async sortNotes(noteGroups: NoteGroup<UserNote>) {
      const notes = [] as UserNote[];
      sortNotes(noteGroups, (n) => {
        notes.push(n);
      });
      this.notes = notes;
      const res = await $fetch<{id: string; parent: string|null; order: number}[]>(`/api/v1/pentestusers/self/notes/sort/`, {
        method: 'POST',
        body: notes.map(n => pick(n, ['id', 'parent', 'order']))
      });
      for (const note of this.notes) {
        const no = res.find(n => n.id === note.id);
        note.parent = no?.parent || null;
        note.order = no?.order || 0;
      }
    },
    async createNote(note: UserNote) {
      note = await $fetch<UserNote>(`/api/v1/pentestusers/self/notes/`, {
        method: 'POST',
        body: note
      });
      this.notes.push(note);
      return note;
    },
    async partialUpdateNote(note: UserNote, fields?: string[]) {
      note = await $fetch<UserNote>(`/api/v1/pentestusers/self/notes/${note.id}/`, {
        method: 'PATCH',
        body: fields ? pick(note, fields.concat(['id'])) : note,
      });
      return this.setNote(note);
    },
    setNote(note: UserNote) {
      const noteIdx = this.notes.findIndex(n => n.id === note.id)
      if (noteIdx !== -1) {
        this.notes[noteIdx] = note;
      } else {
        this.notes.push(note);
      }
      return note;
    },
    async deleteNote(note: UserNote) {
      await $fetch(`/api/v1/pentestusers/self/notes/${note.id}/`, {
        method: 'DELETE'
      });
      this.notes = this.notes.filter(n => n.id !== note.id);
    }
  }
})
