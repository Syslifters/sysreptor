import { PluginIFrame } from '#components';
import type { RouteRecordRaw } from '#vue-router';
import { trimStart } from 'lodash-es';
import { PluginRouteScope } from '#imports';


export function usePluginHelpers(pluginHelperOptions: { pluginConfig: PluginConfig }) {
  const router = useRouter();
  const pluginStore = usePluginStore();

  function addRoute(options: {
    scope: PluginRouteScope;
    route: RouteRecordRaw;
    menu?: Pick<PluginMenuEntry, 'title'|'icon'|'attrs'>;
  }) {
    const routeOptions = {
      ...options.route,
      path: `${pluginHelperOptions.pluginConfig.id}/${trimStart(options.route.path || '', '/')}`,
      name: `plugin-${pluginHelperOptions.pluginConfig.id}-${options.scope}-${options.route.path}`,
    }

    if (options.scope === PluginRouteScope.MAIN) {
      router.addRoute('plugins-main', routeOptions);
    } else if (options.scope === PluginRouteScope.PROJECT) {
      router.addRoute('plugins-project', routeOptions);
    } else {
      throw new Error(`Invalid scope: ${options.scope}`);
    }

    if (options.menu) {
      pluginStore.menuEntries.push({
        ...options.menu,
        scope: options.scope,
        to: { name: routeOptions.name },
      });
    }
  }

  function iframeComponent(props: { src: string, [key: string]: any }) {
    if (pluginHelperOptions?.pluginConfig?.id) {
      props.src = `/static/plugins/${pluginHelperOptions.pluginConfig.id}/${trimStart(props.src || '', '/')}`;
    }

    return Promise.resolve(defineComponent(() => {
      return () => h(PluginIFrame, props);
    }));
  }

  return {
    addRoute,
    iframeComponent,
  }
}


export async function loadPlugin(pluginConfig: PluginConfig) {
  if (pluginConfig.frontend_entry) {
    // try {
      // eslint-disable-next-line no-console
      console.log(`Initializing plugin: ${pluginConfig.name} (plugin_id=${pluginConfig.id})`);
      const frontendEntry = await import(/* @vite-ignore */ pluginConfig.frontend_entry);
      await Promise.resolve(frontendEntry?.default({
        pluginConfig,
        pluginHelpers: usePluginHelpers({ pluginConfig }),
        nuxtApp: useNuxtApp(),
      }));
    // }
    // catch (error) {
    //   // eslint-disable-next-line no-console
    //   console.error(`Failed to initialize plugin: ${pluginConfig.name} (plugin_id=${pluginConfig.id})`, error);
    // }
  }
}

export default defineNuxtPlugin({
  enforce: 'post',
  hooks: {
    async 'app:created'() {
       // Load and initilaize plugins
      const apiSettings = useApiSettings();
      await Promise.all(apiSettings.settings!.plugins.map(loadPlugin));
    }
  },
})
