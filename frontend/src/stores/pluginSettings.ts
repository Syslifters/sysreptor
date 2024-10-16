import type { PluginMenuEntry } from "#imports";

export const usePluginStore = defineStore('pluginStore', {
  state: () => ({
    menuEntries: [] as PluginMenuEntry[],
  }),
});
