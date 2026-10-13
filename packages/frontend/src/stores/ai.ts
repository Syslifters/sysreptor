import { defineStore } from 'pinia';

export const useAiSettings = defineStore('aiSettings', {
  state: () => ({
    openTabs: {} as Record<string, string[]>,
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
  },
  persist: {
    storage: localStorage,
  },
});
