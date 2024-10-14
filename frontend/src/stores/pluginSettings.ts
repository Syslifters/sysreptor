import type { PluginMenuEntry } from "~/utils/types";

export const usePluginStore = defineStore('pluginStore', {
  state: () => ({
    menuEntries: [] as PluginMenuEntry[],
  }),
});
