export default function (options) {
  options.pluginHelpers.addRoute({
    scope: 'project',
    route: {
      path: '',
      component: () => options.pluginHelpers.iframeComponent(({ route }) => {
        const params = new URLSearchParams(window.location.hash.slice(1));
        params.set('projectId', route.params.projectId);
        return {
          src: `index.html#${params.toString()}`,
        }
      }),
    },
    menu: {
      title: 'Excalidraw',
      icon: 'mdi-drawing',
    },
  });
}
