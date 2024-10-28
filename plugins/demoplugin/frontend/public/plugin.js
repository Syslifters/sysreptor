/**
 * This is the plugin frontend entry point.
 * It is called once while loading the single page application in the client's browser.
 * Register plugin routes here and perform initializations.
 */
export default function (options) {
  // Register a new route and add it to the main menu
  options.pluginHelpers.addRoute({
    scope: 'main',
    route: {
      // Relative path, prefixed with "/plugins/<plugin_id>/"
      path: 'demopluginmodels',  
      // Load frontend pages in iframe
      component: () => options.pluginHelpers.iframeComponent({ 
        // Relative path to "/static/plugins/<plugin_id>/" => load "index.html" from the plugin's static directory
        src: 'index.html#/demopluginmodels',  
      }),
    },
    menu: {
      title: 'Demo Plugin',
    }
  });
  // Register a sub-page
  options.pluginHelpers.addRoute({
    scope: 'main',
    route: {
      // Add a path parameter "demopluginmodelId" to the route
      path: 'demopluginmodels/:demopluginmodelId()', 
      // and pass it to the iframe URL
      component: () => options.pluginHelpers.iframeComponent(({ route }) => ({
        src: `index.html#/demopluginmodels/${route.params.demopluginmodelId}`
      })),
    },
    menu: undefined,  // Do not add this route to the main menu
  });

  // Register a per-project route and add it to the project menu
  options.pluginHelpers.addRoute({
    scope: 'project',
    route: {
      // Prefixed with /projects/<projectId>/plugins/<plugin_id>/
      path: '',
      component: () => options.pluginHelpers.iframeComponent(({ route }) => ({
        src: `index.html#/projects/${route.params.projectId}/`,
      }))
    },
    menu: {
      title: 'Demo Plugin',
    },
  });
}
