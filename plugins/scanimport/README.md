# Scan Import Plugin

The Scan Import Plugin allows you to import scan results from various security testing tools into SysReptor. It automatically parses scan output files and converts them into findings or notes.

## Installation

Add `scanimport` to the `ENABLED_PLUGINS` variable in your `app.env` and restart your containers using `docker compose up -d` from the `deploy` directory.

```
ENABLED_PLUGINS="scanimport"
```

## Features

- **Multi-tool Support**: Import results from popular security scanning tools
- **Auto-detection**: Automatically detects file format and selects appropriate parser
- **Partial import**: Select specific findings/notes to import
- **Customize findings**: Allows customizing finding contents via SysReptor templates

## Supported Tools

The plugin currently supports the following security testing tools:

| Tool | File Format | Import Type | Description |
|------|-------------|-------------|-------------|
| **Burp Suite** | XML | Findings/Notes | Web application security scanner |
| **Nessus** | .nessus (XML) | Findings/Notes | Vulnerability scanner |
| **Nmap** | XML/Greppable | Findings/Notes | Network discovery and security auditing |
| **OpenVAS** | XML | Findings/Notes | Vulnerability assessment system |
| **Qualys** | XML | Findings/Notes | Cloud security and compliance platform |
| **SSLyze** | JSON | Findings/Notes | SSL/TLS configuration scanner |
| **OWASP ZAP** | XML/JSON | Findings/Notes | Web application security scanner |


## Customize Findings

The Scan Import Plugin uses SysReptor's finding template system to customize how imported findings are formatted and displayed. This allows you to control exactly how scan results appear in your reports.

### How Templates Work

The plugin selects templates for findings using a hierarchical tag system:

1. **Specific finding templates**: `scanimport:{tool}:{finding_type}` - Used for specific finding types (e.g., `scanimport:nessus:12345`)
2. **General tool templates**: `scanimport:{tool}` - Used for all findings from a specific tool (e.g., `scanimport:nessus`)
3. **Fallback templates**: Built-in templates when no custom template is found


### Template Language

The plugin uses a modified Django template language with HTML comment delimiters to avoid conflicts with Markdown:

- **Variables**: `<!--{{ variable_name }}-->`
- **Control structures**: `<!--{% if condition %}-->...<!--{% endif %}-->`
- **Loops**: `<!--{% for item in items %}-->...<!--{% endfor %}-->`
- **Filters**: `<!--{{ variable|filter }}-->`

See https://docs.djangoproject.com/en/stable/ref/templates/language/ for details.


### Template Variables

Each tool provides different variables based on its output format.


### Creating Custom Templates

1. **Create a Finding Template** in SysReptor with appropriate tags
2. **Add the template tag** (e.g., `scanimport:burp`)
3. **Design your template** using the available variables


### Template Fields

You can map imported data to any custom fields defined in your SysReptor design:

- **Standard fields**: `title`, `summary`, `description`, `recommendation`, `cvss`
- **Custom fields**: Any fields you've defined in your project design
- **Severity mapping**: Automatic severity level conversion with emoji indicators

### Field Mapping Examples

~~~python
# In your template's data:
{
  "tags": ["scanimport:nessus:12345"],  # Template selector tag for mapping
  "title": "Custom finding title or <!--{{ title }}-->",
  "cvss": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
  "severity": "critical",
  "summary": "<!--{{ synopsis }}-->",
  "description": """
    Provide your own finding description here 
    or include (parts of) the imported description via variables.

    <!--{{ description }}-->

    Plugin outputs:

    <!--{% for o in plugin_output %}-->
    ```
    <!--{{ o }}-->
    ```
    <!--{% endfor %}-->
    """,
  "recommendation": """
    To fix the issue, Nessus recommends:

    <!--{{ recommendation }}-->
    """
}
~~~
