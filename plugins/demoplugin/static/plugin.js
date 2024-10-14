function modifyTheme(options) {
  // Modify theme
  const themeLight = options.nuxtApp.$vuetify.theme.themes.value.light;
  themeLight.colors.background = '#ff0000';
  themeLight.colors.surface = '#ff0000';

  // Override CSS styles
  const styleEl = document.createElement('style');
  styleEl.textContent = `
    .v-theme--dark {
      --v-theme-background: 0 0 255;
      --v-theme-surface: 0 0 255;
    }
  `;
  document.body.appendChild(styleEl);
}


function registerPages(options) {
 // Top-level page as iframe
 options.pluginHelpers.addRoute({
   parent: 'main',
   route: {
     path: 'iframe',
     component: options.pluginHelpers.iframeComponent({ src: 'iframe.html' }),
   },
 });

//  // Top-level page with menu entry
//  options.pluginHelpers.addRoute({
//    parent: 'main',
//    route: {
//      path: 'demoplugin',
//      component: () => import('./components/TheWelcome.vue'),
//      children: [
//        {
//          path: ':subpageId()',
//          component: () => import('./components/TheWelcome.vue'),
//        }
//      ],
//    },
//    menu: {
//      name: 'Demo Plugin',
//      icon: 'mdi-puzzle',
//    },
//  });
//  // Per-project page with menu entry
//  options.pluginHelpers.addRoute({
//    parent: 'project',
//    route: {
//      path: 'demoplugin',
//      component: () => import('./components/TheWelcome.vue'),
//    },
//    menu: {
//      name: 'Demo Plugin',
//      icon: 'mdi-puzzle',
//    }
//  });
}


export default function(options) {
 console.log('Hello from demoplugin');

 // modifyTheme(options);
 registerPages(options);
}