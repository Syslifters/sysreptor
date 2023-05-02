import { apmBase } from '@elastic/apm-rum';
import { getErrorHandler } from '@elastic/apm-rum-vue/dist/lib/error-handler';
import { routeHooks } from "@elastic/apm-rum-vue/dist/lib/route-hooks";
import Vue from 'vue';

Vue.use({
  install(app) {
    app.config.errorHandler = getErrorHandler(app, apmBase);
  }
});

export default async function apiSettingsPlugin({ app, store }) {
  // Load api settings
  await store.dispatch('apisettings/getSettings');

  // Enable Elastic APM RUM
  const apmRumConfig = store.getters['apisettings/settings'].elastic_apm_rum_config;
  if (apmRumConfig) {
    apmBase.init(apmRumConfig);
    routeHooks(app.router, apmBase);
  }
}
