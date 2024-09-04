// @ts-expect-error missing types
import { ApmVuePlugin } from '@elastic/apm-rum-vue'

export default defineNuxtPlugin(async (nuxtApp) => {
  const localSettings = useLocalSettings();
  const apiSettings = useApiSettings();
  await apiSettings.getSettings();

  // Enable Elastic APM RUM
  const apmRumConfig = apiSettings.settings!.elastic_apm_rum_config;
  if (apmRumConfig) {
    const router = useRouter();
    nuxtApp.vueApp.use(ApmVuePlugin, {
      config: apmRumConfig,
      captureErrors: true,
      router,
    });
  }

  return {
    provide: {
      localSettings,
      apiSettings
    },
  }
});
