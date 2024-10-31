export default function(options) {
  const routeConfig = {
    route: {
      path: '',
      component: () => options.pluginHelpers.iframeComponent(({ _ }) => { 
        return {
          src: 'voyager/index.html'
        };
      }),
    },
    menu: {
      title: 'GraphQL Voyager',
      icon: 'mdi-graph',
    },
  };
  options.pluginHelpers.addRoute({
    scope: 'main',
    ...routeConfig,
  });
  options.pluginHelpers.addRoute({
    scope: 'project',
    ...routeConfig,
  });
}
