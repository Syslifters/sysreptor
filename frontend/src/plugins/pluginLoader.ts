import type { RouteRecordRaw, RouteLocationNormalizedLoadedGeneric } from '#vue-router';
import { trimStart } from 'lodash-es';
import type { ThemeInstance } from 'vuetify';
import { PluginRouteScope } from '#imports';
import { PluginIFrame } from '#components';


export type PluginIframeSrc = string|((options: { 
  route: RouteLocationNormalizedLoadedGeneric;
  user: User;
  theme: ThemeInstance;
}) => string);


export type PluginIFrameAttrs = {
  src: string;
  [key: string]: any;
};

export type PluginIFrameComponentProps = 
  PluginIFrameAttrs | 
  ((options: {
    route: RouteLocationNormalizedLoadedGeneric;
    user: User;
    theme: ThemeInstance;
  }) => PluginIFrameAttrs);


export function usePluginHelpers(pluginHelperOptions: { pluginConfig: PluginConfig }) {
  const router = useRouter();
  const auth = useAuth();
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
        pluginConfig: pluginHelperOptions.pluginConfig,
      });
    }
  }

  function iframeComponent(props: PluginIFrameComponentProps) {
    return Promise.resolve(defineComponent(() => {
      let attrs = props as PluginIFrameAttrs;
      if (typeof props === 'function') {
        // Build dynamic src
        attrs = props({
          route: router.currentRoute.value,
          user: auth.user.value!,
          theme: useTheme(),
        });
      }
      let iframeSrc = attrs.src;
      if (!iframeSrc.startsWith('/') && !iframeSrc.startsWith('https://') && !iframeSrc.startsWith('http://')) {
        // Convert relative src to absolute
        if (iframeSrc.startsWith('api/')) {
          iframeSrc = `/api/plugins/${pluginHelperOptions.pluginConfig.id}/${iframeSrc}`;
        } else {
          iframeSrc = `/static/plugins/${pluginHelperOptions.pluginConfig.id}/${iframeSrc}`;
        }
      }

      return () => h(PluginIFrame, {
        ...attrs,
        src: iframeSrc,
      });
    }));
  }

  return {
    addRoute,
    iframeComponent,
  }
}


export async function loadPlugin(pluginConfig: PluginConfig) {
  if (pluginConfig.frontend_entry) {
    const nuxtApp = useNuxtApp();
    try {
      // eslint-disable-next-line no-console
      console.log(`Initializing plugin: ${pluginConfig.name} (plugin_id=${pluginConfig.id})`);
      const frontendEntry = await import(/* @vite-ignore */ pluginConfig.frontend_entry);
      await Promise.resolve(frontendEntry?.default({
        pluginConfig,
        pluginHelpers: usePluginHelpers({ pluginConfig }),
        nuxtApp,
        theme: nuxtApp.$vuetify.theme,
      }));
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.error(`Failed to initialize plugin: ${pluginConfig.name} (plugin_id=${pluginConfig.id})`, error);
    }
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
