import type { ProjectNote, ShareInfoPublic } from "~/utils/types";

export const useShareInfoStore = defineStore('shareinfo', {
  state: () => {
    return {
      data: null as null|{
        shareInfo: ShareInfoPublic,
        notesCollabState: CollabStoreState<{ notes: Record<string, ProjectNote>}>
      }
    };
  },
  getters: {
    notes(): ProjectNote[] {
      return Object.values(this.data?.notesCollabState.data.notes || {});
    },
    noteGroups(): NoteGroup<ProjectNote> {
      return groupNotes(this.notes);
    },
  },
  actions: {
    clear() {
      this.useNotesCollab().disconnect();
      this.data = null;
    },
    async fetchById(shareId: string) {
      const shareInfo = await $fetch<ShareInfoPublic>(`/api/v1/shareinfos/${shareId}/`);
      this.data = {
        shareInfo,
        notesCollabState: makeCollabStoreState({
          apiPath: `/ws/shareinfos/${shareId}/notes/`,
          initialData: { notes: {} as Record<string, ProjectNote> },
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
          },
        }),
      };
      return this.data.shareInfo;
    },
    async getById(shareId: string) {
      if (this.data?.shareInfo.id === shareId) {
        return this.data.shareInfo;
      } else {
        return await this.fetchById(shareId);
      }
    },
    async createNote(shareInfo: ShareInfoPublic, note: ProjectNote) {
      note = await $fetch<ProjectNote>(`/api/v1/shareinfos${shareInfo.id}/notes/`, {
        method: 'POST',
        body: note
      });
      if (this.data?.shareInfo.id === shareInfo.id) {
        this.data.notesCollabState.data.notes[note.id] = note;
      }
      return note;
    },
    async deleteNote(shareInfo: ShareInfoPublic, note: UserNote) {
      await $fetch(`/api/v1/shareinfos/${shareInfo.id}/notes/${note.id}/`, {
        method: 'DELETE'
      });
      if (this.data?.shareInfo.id === shareInfo.id) {
        delete this.data.notesCollabState.data.notes[note.id];
      }
    },
    useNotesCollab(options?: { shareInfo: ShareInfoPublic, noteId?: string }) {
      if (this.data?.shareInfo.id !== options?.shareInfo.id) {
        throw new Error('ShareInfo not loaded');
      }

      const collabState = this.data!.notesCollabState;
      const collab = useCollab(collabState as CollabStoreState<{ notes: Record<string, ProjectNote> }>);

      return {
        ...collab,
        collabProps: computed(() => collabSubpath(collab.collabProps.value, options?.noteId ? `notes.${options.noteId}` : null)),
      }
    },
  },
});
