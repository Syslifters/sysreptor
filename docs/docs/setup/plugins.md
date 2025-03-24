# Plugins
<span style="color:orange;">:octicons-alert-fill-24: Experimental. Expect breaking changes.</span>

SysReptor provides a plugin system to extend the functionality of the application without modifying the SysReptor core code.
Plugins can hook into the SysReptor core and provide additional features both in the API and the web UI.

All plugins are disabled by default. To enable a plugin, add the [`ENABLED_PLUGINS`](./configuration.md#plugins) variable to your app.env (e.g., `ENABLED_PLUGINS=cyberchef,checkthehash`) and restart your container (`docker compose up -d` from the `deploy` directory).


## Official Plugins

:octicons-server-24: Self-Hosted :octicons-cloud-24: Cloud

Official plugins are maintained by the SysReptor team and are shipped inside official docker images.

| Plugin | Description |     |
| ------ | ----------- | --- |
| [cyberchef](https://github.com/Syslifters/sysreptor/tree/main/plugins/cyberchef) | CyberChef integration | |
| [graphqlvoyager](https://github.com/Syslifters/sysreptor/tree/main/plugins/graphqlvoyager) | GraphQL Voyager integration | |
| [checkthehash](https://github.com/Syslifters/sysreptor/tree/main/plugins/checkthehash) | Hash identifier | |
| [customizetheme](https://github.com/Syslifters/sysreptor/tree/main/plugins/customizetheme) | Customize UI themes per instance | |
| [demoplugin](https://github.com/Syslifters/sysreptor/tree/main/plugins/demoplugin) | A demo plugin that demonstrates the plugin system | |
| [projectnumber](https://github.com/Syslifters/sysreptor/tree/main/plugins/projectnumber) | Automatically adds an incremental project number to new projects | |
| [webhooks](https://github.com/Syslifters/sysreptor/tree/main/plugins/webhooks) | Send webhooks on certain events | <span style="color:red;">:octicons-heart-fill-24: Pro only</span> |
| [renderfindings](https://github.com/Syslifters/sysreptor/tree/main/plugins/renderfindings) | Render selected findings to pdf | <span style="color:red;">:octicons-heart-fill-24: Pro only</span> |





## Developing Custom Plugins
:octicons-server-24: Self-Hosted

It is possible to develop and load custom plugins to extend the functionality of SysReptor.
Custom plugins are only supported in self-hosted installations, but not in the cloud version.

### Getting Started
We recommend to develop and manage custom plugins in a separate Git repository, not in the SysReptor repository.
First, you need to set up a new repository (either on GitHub or your internal version control system) with a directory structure similar to:

```
plugin-repository
├── .gitignore
├── .dockerignogre
├── Dockerfile
├── sysreptor.docker-compose.override.yml
├── custom_plugins/
│   ├── myplugin1/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── signals.py
│   │   ├── ...other .py files
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── test_myplugin1.py
│   │   ├── migrations/
│   │   │   ├── __init__.py
│   │   │   └── ...auto-generated migrations
│   │   └── static/
│   │       ├── plugin.js
│   │       └── ...other HTML, CSS, JS assets
│   ├── myplugin2/
│   │   └── ...
│   └── ...additional plugins
└── ...additional top-level files
```

We recommend to create a parent directory that contains all your custom plugins (e.g. `custom_plugins`).
Plugin directories should contain a valid SysReptor plugin structure that can be loaded by the SysReptor core.
Use [demoplugin](https://github.com/Syslifters/sysreptor/tree/main/plugins/demoplugin) as a starting point.

!!! note "Use a unique `plugin_id` and module name."

    When copying an existing plugin, make sure to change the module (plugin directory) name 
    and to change the `plugin_id` in `apps.py`.


### Plugin Loading
Custom plugins need to be made available to the SysReptor docker container.
This can be achived by extending the SysReptor docker image and adding your custom plugins to the image.

```dockerfile title="Dockerfile example"
ARG SYSREPTOR_VERSION="latest"

# Optional build stage for frontend assets
FROM node:22-alpine3.20 AS plugin-builder
# Build frontend assets
COPY custom_plugins /custom_plugins
RUN cd /custom_plugins/myplugin1/frontend && npm install && npm run generate

# Extend the Sysreptor image with custom plugins
FROM syslifters/sysreptor:${SYSREPTOR_VERSION}
# Optional: install additional dependencies
# RUN pip install ...
ENV PLUGIN_DIRS=${PLUGIN_DIRS}:/custom_plugins
COPY --from=plugin-builder /custom_plugins /custom_plugins
```

Use following code snippets to plug your extended docker image to the SysReptor docker-compose file:

!!! note 

    Directly modifying `sysreptor/deploy/sysreptor/docker-compose.yml` is not recommended, because changes might get overwritten during [updates](/setup/updates.md).
    The presented way is compatible with the `update.sh` script.


First, modify `sysreptor/deploy/docker-compose.yml` to add an include docker compose include file.

```yaml title="sysreptor/deploy/docker-compose.yml"
name: sysreptor

include:
  - path:
      - sysreptor/docker-compose.yml
      # Path to sysreptor.docker-compose.override.yml in your plugin repository
      # Note: Path is relative to sysreptor/deploy/docker-compose.yml (or an absolute path)
      - ../../plugin-repository/sysreptor.docker-compose.override.yml
```

The content of `../../plugin-repository/sysreptor.docker-compose.override.yml` is merged with the original `sysreptor/docker-compose.yml` (from SysReptor core)
and allows extending or overriding docker compose configurations.
See https://docs.docker.com/reference/compose-file/include/ for more information about docker compose includes.


Then, override the `image` and `build` options in `sysreptor.docker-compose.override.yml` to use your extended SysReptor docker image with custom plugins included.
Note that paths in this file are relative to the `sysreptor/deploy` directory (from SysReptor core docker compose file).

```yaml title="sysreptor.docker-compose.override.yml example"
services:
  app:
    # Override the docker image
    image: !reset null
    build: 
      # Note: Path is relative to sysreptor/deploy/docker-compose.yml (or an absolute path)
      context: ../../plugin-repository
      args:
        SYSREPTOR_VERSION: ${SYSREPTOR_VERSION:-latest}
```



### Server-side Plugin
SysReptor plugins are Django apps can hook into the SysReptor core and provide additional functionality.
See the [Django documentation](https://docs.djangoproject.com/en/stable/ref/applications/) and [Django app tutorial](https://docs.djangoproject.com/en/stable/intro/tutorial01/) for more information about Django apps.

Each plugin needs at least an `__init__.py` and `apps.py` file with a minimal plugin configuration.
Use the [demoplugin](https://github.com/Syslifters/sysreptor/tree/main/plugins/demoplugin) as a starting point.

```python title="apps.py example"
--8<-- "../plugins/demoplugin/apps.py"
```

Besides `apps.py`, you can add arbitrary Python files to the plugin directory to structure your plugin code.
We recommend to stick to the Django app structure:

* `models.py` for database model classes
* `migrations/` directory for database migrations
* `admin.py` for Django admin configuration for your models
* `urls.py` for URL routing: URLs in variable `urlpatterns` are registered at `/api/plugins/<plugin_id>/api/...`
* `views.py` for API views e.g. [Django REST framework](https://www.django-rest-framework.org/) viewsets
* `serializers.py` for Django REST framework serializers
* `signals.py` for signal handlers listening to Django or SysReptor signals
* `static/` directory for static assets (e.g. JS, CSS, images): served at `/static/plugins/<plugin_id>/...`
  * `plugin.js` is the entrypoint for frontend plugins
* `tests/` directory for unit tests (highly recommended)


#### Python Imports and Dependencies
You are able to import and reuse modules from SysReptor core as well as other third-party libraries that are installed in the server's python environment (e.g. django).
Please note that the SysReptor core and third-party libraries are subject to change and updates, so be aware of potential breaking changes when importing internal modules.
In order to detect breaking changes early, we recommend writing [unit tests](#testing) for your plugin code.

When importing modules from your own plugin, prefer relative imports over absolute imports.

```python title="imports example"
# Prefer relative imports
from .models import DemoPluginModel
# over absolute imports
from sysreptor_plugins.demoplugin.models import DemoPluginModel
```

Plugins are able to reuse existing third-party libraries that are installed in the server's python environment.
If you need to install additional dependencies, you need to extend the `Dockerfile` and install the dependencies via `pip`.



#### Database models
If your plugin needs to store data in the database, you can define Django models in `models.py`.
You also need to create database migrations for your models to create/update the database schema.
SysReptor automatically applies plugin migrations on startup if the plugin is enabled
and also includes plugin models in [backups and restores](/setup/backups.md).

Here are the basic steps to create a Django models:

* Define your django model classes in `models.py`
* Create a `migrations/` directory and `migrations/__init__.py` file
* Ensure your plugin is loaded and enabled
* Run `docker compose run --rm app python3 manage.py makemigrations` to create the initial migration files
* Run `docker compose run --rm api python3 manage.py migrate` to apply the migrations

See the Django documentation for more information:
* https://docs.djangoproject.com/en/stable/topics/db/models/
* https://docs.djangoproject.com/en/stable/topics/migrations/


#### API Endpoints
You can define API endpoints in your plugin by defining API views in `views.py` and registering them in URL patterns to `urls.py`.

```python title="urls.py example"
--8<-- "../plugins/demoplugin/urls.py"
```

API views can be implemented as Django views or [Django REST framework](https://www.django-rest-framework.org/) viewsets.

```python title="views.py example"
--8<-- "../plugins/demoplugin/views.py"
```

Django REST framework uses serializers to serialize and deserialize data between Python objects and JSON.
Define your serializers in `serializers.py`.

```python title="serializers.py example"
--8<-- "../plugins/demoplugin/serializers.py"
```


#### Signals
Plugins can listen to [Django signals](https://docs.djangoproject.com/en/stable/topics/signals/) to react to certain events in the SysReptor core.
SysReptor provides additional signals that are not part of Django in the `sysreptor.signals` module.

Signal handlers should be defined in your plugin's `signals.py` file.
In order to load the signal handlers, you need to register them in the `ready()` method of your plugin's `apps.py`.

```python title="apps.py example"
class DemoPluginConfig(PluginConfig):
    def ready(self):
        from . import signals  # noqa
```

```python title="signals.py example"
--8<-- "../plugins/demoplugin/signals.py"
```


#### Testing
We highly recommend writing unit tests for your plugins.
Unit tests ensure that

* your plugins work as expected and help in detecting breaking changes early
* detect when updates of SysReptor core break your plugins
* detect when your plugins break SysReptor core (especially when using signal handlers)

Unit tests should be placed in the `tests/` directory of your plugin.
[`pytest`](https://docs.pytest.org/en/stable/) and [`pytest-django`](https://pytest-django.readthedocs.io/en/latest/) are available in the SysReptor container and can be used to run your tests.

```python title="test.py example"
--8<-- "../plugins/demoplugin/tests/test_api.py"
```

Run unit tests:

```bash
# Test a single plugin
docker compose run --rm -e ENABLED_PLUGINS=demoplugin app pytest sysreptor_plugins/demoplugin
# Run all tests (core + all plugins)
docker compose run --rm -e ENABLED_PLUGINS='*' app pytest -n auto
```


### Frontend Plugin
Frontend plugins hook into the SysReptor web UI (single page application) and can register new menu entries and pages.


#### Frontend Plugin Entrypoint
Frontend plugins are loaded from the `/static/` directory and need to provide pre-built assets.
The entrypoint for frontend plugins is `plugin.js` in the `static/` directory.
`plugin.js` should perform setup actions for the frontend plugin, e.g. registering new menu entries and pages.

```javascript title="plugin.js example"
--8<-- "../plugins/demoplugin/frontend/public/plugin.js"
```

Plugins can register new pages in the SysReptor web UI via `options.pluginHelpers.addRoute()`.
Pages are loaded in `iframes` to provide the most flexibility for loaded content.
HTML files loaded as `iframes` as well as any other assets (e.g. JS, CSS, images) should be placed in the `static/` directory.

The SysReptor web application uses session cookies for authentication, so you are able to access the SysReptor API from within plugin `iframes`.


#### Vue/Nuxt Pages
SysReptor provides some Vue/Nuxt UI components to be reused in plugins to ensure a consistent look and feel.
For that, you need to introduce an additional build step to compile your Vue/Nuxt pages into static assets that can be loaded in `iframes`.
We recommend to place your Vue/Nuxt code in the `frontend/` directory of your plugin and write output files to the `static/` directory.

SysReptor provides the [Nuxt Layer](https://nuxt.com/docs/getting-started/layers) `plugin-base-layer`.
This layer contains basic plugin configurations and UI components that can be used in plugins.
See https://github.com/Syslifters/sysreptor/tree/main/plugins/demoplugin/frontend for an example setup.

To build the frontend assets, you need to run the following commands:

```bash
cd demoplugin/frontend
# Install JS dependencies
npm install
# Build the frontend assets
npm run generate
```

Here are some notes to get you started:

* See the [Nuxt documentation](https://nuxt.com/) for the basic setup and configuration
* URLs to other SysReptor pages (also from the same plugin): 
  * use full paths with plugin ID
  * e.g. `/plugins/${pluginId}/...` or `/projects/${projectId}/plugins/${pluginId}/...`
* navigate to other SysReptor pages: 
  * from inside plugin `iframes` you need to perform a top-level navigation to not load the page inside the `iframe`
  * set `<a href="..." target="_top">` or use `await navigateTo(..., { open: { target: "_top" } })`
* fetch data from plugin API: 
  * use full URLs with plugin ID
  * e.g. `/api/plugins/${pluginId}/api/...`
* importing components:
  * components (from nuxt-base-layer and local component) are auto-imported
  * if you want to import them explicitely use `import { ... } from '#components'`
  * composables, utilities, etc. (from nuxt-base-layer and local) can be imported via `import { ... } from '#imports'`

