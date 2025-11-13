# Customize Theme

This plugin allows to customize the theme of the SysReptor frontend.
It allows to change settings of light and dark themes globally per instance.



## Configuration
`PLUGIN_CUSTOMIZETHEME_CONFIG` accepts a JSON object with theme configs. 
The provided configurations override the [default theme configs](../../packages/nuxt-base-layer/src/vuetify.config.ts).
All theme configurations provided by Vuetify are supported. See the [Vuetify documentation](https://vuetifyjs.com/en/features/theme/) for more information.
Options in `all` apply to both light and dark mode. Options in `light` and `dark` apply to the respective mode only.

```
ENABLED_PLUGINS="customizetheme"
PLUGIN_CUSTOMIZETHEME_CONFIG='{"light": {...}, "dark": {...}, "all": {...}}'
```


## Examples
### Custom Risk Colors
You want to use the same colors for risk levels in the web UI as in the report PDFs?

```json
{
  "all": {
    "colors": {
       "risk-critical": "#8c00fc",
       "risk-high": "#ed0003",
       "risk-medium": "#f0d400",
       "risk-low": "#009dff",
       "risk-info": "#00bc00"
    }
  }
}
```

### Header with Corporate Colors and Logo
```json
{
  "all": {
    "colors": {
      "header": "#ff00ff"
    },
    "variables": {
      "header-logo-url": "data:image/svg+xml;base64,..."
    }
  }
}
```

Note: `header-logo-url` is only applied in SysReptor Pro

### Matrix Dark Theme
```json
{
  "dark": {
    "colors": {
      "on-background": "#74ee15",
      "on-surface": "#74ee15",
      "on-drawer": "#74ee15",
      "on-header": "#74ee15"
    }
  }
}
```
