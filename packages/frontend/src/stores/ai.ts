import { defineStore } from 'pinia';

export const useAiSettings = defineStore('aiSettings', {
  state: () => ({
    openTabs: {} as Record<string, string[]>,
    acceptedChangesUpTo: {} as Record<string, Record<string, string>>,
  }),
  actions: {
    getOpenTabs(projectId: string): string[] {
      return this.openTabs?.[projectId] || [];
    },

    setOpenTabs(projectId: string, threadIds: string[]) {
      this.openTabs = {
        ...this.openTabs,
        [projectId]: threadIds,
      };
    },

    getAcceptedChangesUpTo(threadId: string): Record<string, string> {
      return this.acceptedChangesUpTo?.[threadId] ?? {};
    },

    acceptChangesUpTo(threadId: string, entityId: string, timestamp: string) {
      const current = { ...(this.acceptedChangesUpTo?.[threadId] || {}) };
      const prev = current[entityId];
      if (!prev || timestamp > prev) {
        current[entityId] = timestamp;
      }
      this.acceptedChangesUpTo = {
        ...this.acceptedChangesUpTo,
        [threadId]: current,
      };
    },
  },
  persist: {
    storage: localStorage,
  },
});
