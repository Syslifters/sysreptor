export default function (options) {
  options.pluginHelpers.addRoute({
    scope: 'project',
    route: {
      path: '',
      component: () => options.pluginHelpers.iframeComponent(({ route }) => ({
        src: `index.html#projectId=${route.params.projectId}`,
      }))
    },
    menu: {
      title: 'Excalidraw',
      icon: 'mdi-drawing',
    },
  });
}
