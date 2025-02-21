import type { PluginMenuEntry } from "#imports";
import { sortBy } from "lodash-es";

export const usePluginStore = defineStore('pluginStore', {
  state: () => ({
    menuEntries: [] as PluginMenuEntry[],
  }),
  getters: {
    menuEntriesOrdered(state) {
      const pluginIdsOrdered = (useApiSettings().settings?.plugins || []).map(p => p.id);
      return sortBy(state.menuEntries, [(e) =>  {
        const idx = pluginIdsOrdered.indexOf(e.pluginConfig.id);
        return idx === -1 ? Infinity : idx;
      }]);
    },
    menuEntriesForScope() {
      return (scope: PluginRouteScope) => this.menuEntriesOrdered.filter(entry => entry.scope === scope);
    },
  }
});

export function pluginUrl(menuEntry: PluginMenuEntry, params?: Record<string, string|string[]|undefined>) {
  const router = useRouter();
  try {
    return router.resolve({...menuEntry.to, params}).href;
  } catch {
    return undefined;
  }
}

