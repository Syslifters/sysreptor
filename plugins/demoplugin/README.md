# Demoplugin

This is a demo plugin that demonstrates the plugin system.
Use this plugin as a reference to develop your own plugins.

Plugins are loaded as [Django apps](https://docs.djangoproject.com/en/stable/ref/applications/). Plugins can add API endpoints, views, models, admin pages, signal handlers, and more.
Data can be stored in the database via Django models. Migrations are supported.

Plugins can extend the frontend by adding pages and menu entries. Each frontend plugin provides an entrypoint script named [`plugin.js`](./frontend/public/plugin.js) as static file. This script is called when the web application is loaded in the browser and performs the necessary plugin setup (e.g. register new routes, add menu entries, etc.).
Plugin pages are loaded as iframes. This allows you to develop frontend plugins with any frontend framework you like, add custom dependencies, or include existing third-party applications.
