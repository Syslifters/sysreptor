import { pick } from "lodash-es";
import type { UserNote } from "#imports";

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
    async copyNote(note: UserNote) {
      const newNote = await $fetch<UserNote>(`/api/v1/pentestusers/self/notes/${note.id}/copy/`, {
        method: 'POST',
        body: {},
      });
      this.notesCollabState.data.notes[newNote.id] = newNote;
      return newNote;
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
