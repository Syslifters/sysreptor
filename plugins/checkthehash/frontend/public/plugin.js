export default function (options) {
  options.pluginHelpers.addRoute({
    scope: 'main',
    route: {
      path: 'check-the-hash',  
      component: () => options.pluginHelpers.iframeComponent({ 
        src: 'index.html#/check-the-hash',  
      }),
    },
    menu: {
      title: 'Check The Hash',
      icon: 'mdi-format-header-pound'
    }
  });
}
