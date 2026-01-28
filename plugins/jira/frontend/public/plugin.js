export default function (options) {
  options.pluginHelpers.addRoute({
    scope: 'project',
    route: {
      path: '',
      component: () => options.pluginHelpers.iframeComponent(({ route }) => ({
        src: `index.html#/projects/${route.params.projectId}/`,
      }))
    },
    menu: {
      title: 'Jira',
      icon: 'mdi-jira',
    },
  });
}
