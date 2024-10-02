import type { ProjectNote, ShareInfoPublic } from "#imports";

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
      return groupNotes(this.notes, { parentNoteId: this.notes.find(n => n.id === this.data?.shareInfo.note_id)?.parent || null });
    },
  },
  actions: {
    async fetchById(shareId: string) {
      const shareInfo = await $fetch<ShareInfoPublic>(`/api/public/shareinfos/${shareId}/`);
      if (this.data?.shareInfo.id !== shareId) {
        this.data = {
          shareInfo,
          notesCollabState: makeCollabStoreState({
            apiPath: `/api/public/ws/shareinfos/${shareId}/notes/`,
            initialData: { notes: {} as Record<string, ProjectNote> },
            initialPath: 'notes',
            handleAdditionalWebSocketMessages: (msgData: any, collabState) => {
              if (msgData.type === CollabEventType.SORT && msgData.path === 'notes') {
                if (msgData.sort.some((sn: ProjectNote) => !Object.values(collabState.data.notes).map(dn => dn.id).includes(sn.id))) {
                  // Non-shared note moved to shared note. Close and reopen WebSocket connection to get updated data.
                  collabState.connection?.disconnect();
                }

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
      } else {
        this.data.shareInfo = shareInfo;
      }
      
      return this.data.shareInfo;
    },
    async getById(shareId: string) {
      if (this.data?.shareInfo.id === shareId) {
        return this.data.shareInfo;
      } else {
        return await this.fetchById(shareId);
      }
    },
    async createNote(shareInfo: ShareInfoPublic, note: Partial<ProjectNote>) {
      const newNote = await $fetch<ProjectNote>(`/api/public/shareinfos/${shareInfo.id}/notes/`, {
        method: 'POST',
        body: note
      });
      if (this.data?.shareInfo.id === shareInfo.id) {
        this.data.notesCollabState.data.notes[newNote.id] = newNote;
      }
      return newNote;
    },
    async deleteNote(shareInfo: ShareInfoPublic, note: UserNote) {
      await $fetch(`/api/public/shareinfos/${shareInfo.id}/notes/${note.id}/`, {
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
      const collabProps = computed(() => collabSubpath(collab.collabProps.value, options?.noteId ? `notes.${options.noteId}` : null));
      
      const apiSettings = useApiSettings();
      const auth = useAuth();
      const hasLock = ref(true);
      if (options?.noteId && !apiSettings.isProfessionalLicense) {
        hasLock.value = false;
        watch(() => collabProps.value.clients, () => {
          if (!hasLock.value && collabProps.value.clients.filter(c => (auth.user.value && c.user?.id !== auth.user.value.id) || c.client_id !== collab.storeState.clientID).length === 0) {
            hasLock.value = true;
          }
        }, { immediate: true });
      }

      return {
        ...collab,
        collabProps,
        hasLock,
        readonly: computed(() => collab.readonly.value || !hasLock.value),
      }
    },
  },
});
