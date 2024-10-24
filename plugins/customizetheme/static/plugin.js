export default function(options) {
  // Modify vuetify theme
  const pluginSettings = options.pluginConfig.frontend_settings;
  const themes = options.theme.themes.value;
  if ('all' in pluginSettings) {
    for (const theme of Object.values(themes)) {
      assignDeep(theme, pluginSettings.all);
    }
  }
  for (const [themeName, theme] of Object.entries(themes)) {
    if (themeName in pluginSettings) {
      assignDeep(theme, pluginSettings[themeName]);
    }
  }

  // Alternatively, directly add CSS styles
  // const styleEl = document.createElement('style');
  // styleEl.textContent = `
  //   :root, .v-theme--light, .v-theme--dark {
  //     --v-theme-risk-critical: ${hexToRgb('#8c00fc')};
  //     --v-theme-risk-high: ${hexToRgb('#ed0003')};
  //     --v-theme-risk-medium: ${hexToRgb('#f0d400')};
  //     --v-theme-risk-low: ${hexToRgb('#009dff')};
  //     --v-theme-risk-info: ${hexToRgb('#00bc00')};
  //   }
  // `;
  // document.body.appendChild(styleEl);
}


function assignDeep(target, source) {
  if (isObject(target) && isObject(source)) {
    for (const key in source) {
      if (isObject(source[key])) {
        if (!target[key]) {
          Object.assign(target, { [key]: {} });
        }
        assignDeep(target[key], source[key]);
      } else {
        Object.assign(target, { [key]: source[key] });
      }
    }
  }
}

function isObject(item) {
  return (item && typeof item === 'object' && !Array.isArray(item));
}
