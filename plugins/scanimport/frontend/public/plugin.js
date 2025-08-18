export default function (options) {
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
      title: 'Scan Import',
      icon: 'mdi-file-upload',
    },
  });
}
