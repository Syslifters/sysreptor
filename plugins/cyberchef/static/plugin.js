export default function(options) {
  const routeConfig = {
    route: {
      path: '',
      component: () => options.pluginHelpers.iframeComponent(({ theme }) => { 
        // Set cyberchef theme before loading
        const cyberchefOptions = JSON.parse(localStorage.getItem('options') || '{}');
        cyberchefOptions.theme = theme.current.value.dark ? 'dark' : 'classic';
        cyberchefOptions.updateUrl = false;
        localStorage.setItem('options', JSON.stringify(cyberchefOptions));

        return {
          src: 'cyberchef/CyberChef_v10.19.2.html'
        };
      }),
    },
    menu: {
      title: 'CyberChef',
      icon: 'mdi-chef-hat',
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