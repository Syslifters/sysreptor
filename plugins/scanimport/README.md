# Scan Import Plugin

The Scan Import Plugin allows you to import scan results from various security testing tools into SysReptor. It automatically parses scan output files and converts them into findings or notes.

This plugin requires SysReptor Professional.

## Installation

Add `scanimport` to the `ENABLED_PLUGINS` variable in your `app.env` and restart your containers using `docker compose up -d` from the `deploy` directory.

```
ENABLED_PLUGINS="scanimport"
```

## Features

- **Multi-tool support**: Import results from popular security scanning tools
- **Auto-detection**: Automatically detects file format and selects the appropriate parser
- **Partial import**: Select specific findings or notes to import
- **Customizable findings**: Control finding contents via SysReptor finding templates

## Supported Tools

| Tool | File Format | Import Type | Description |
|------|-------------|-------------|-------------|
| **Burp Suite** | XML | Findings/Notes | Web application security scanner |
| **Nessus** | .nessus (XML) | Findings/Notes | Vulnerability scanner |
| **Nmap** | XML/Greppable | Notes | Network discovery and security auditing |
| **OpenVAS** | XML | Findings/Notes | Vulnerability assessment system |
| **Prowler** | CSV/JSON (OCSF) | Findings/Notes | AWS/cloud security assessment tool |
| **Qualys** | XML | Findings/Notes | Cloud security and compliance platform |
| **ScoutSuite** | JS/JSON | Findings/Notes | Multi-cloud security auditing tool |
| **SSLyze** | JSON | Findings/Notes | SSL/TLS configuration scanner |
| **OWASP ZAP** | XML/JSON | Findings/Notes | Web application security scanner |

## Customize Findings

The Scan Import Plugin uses SysReptor's finding template system to customize how imported findings are formatted. This lets you control how scan results appear in your reports.

### Import Workflow

1. **(Optional) Create a finding template** in SysReptor and tag it for the importer, e.g. `scanimport:sslyze:weak_tls_setup` or `scanimport:nessus:12345`. If you skip this, the plugin uses its built-in fallback template.
2. **Upload** the scan file(s) in the Scan Import plugin UI and choose **Import as Finding**.
3. **Parse**: The plugin parses the uploaded files. When multiple files are uploaded, findings from all files are merged into one list. SSLyze currently creates a single aggregated finding that contains all targets.
4. **Template lookup**: The plugin selects a template via tags (see [How Templates Work](#how-templates-work)).
5. **Render**: Fields from the matched template are rendered with the modified Django template language. Parsed finding data is available as template variables.
6. **Select and add**: Choose which findings to add to the project. If template rendering succeeds, fields are filled as defined by the template and finding data.

### How Templates Work

The plugin selects templates for findings using a hierarchical tag system:

1. **Specific finding templates**: `scanimport:{tool}:{finding_type}` — used for specific finding types (e.g. `scanimport:nessus:12345`)
2. **Fallback specific finding templates**: built-in templates for specific findings (e.g. `scanimport:sslyze:weak_tls_setup`); currently only used by the `sslyze` importer
3. **General tool templates**: `scanimport:{tool}` — used for all findings from a specific tool (e.g. `scanimport:nessus`)
4. **Fallback templates**: built-in templates when no custom template is found

`{finding_type}` is tool-specific (e.g. Nessus plugin ID, Burp issue type, OpenVAS OID, ZAP alert reference, Qualys QID, Prowler check ID, ScoutSuite finding ID).

Because a specific tag is tried before a general one, a built-in specific template outranks a custom general tool template. For example, SSLyze ships a built-in template tagged `scanimport:sslyze:weak_tls_setup`. A custom template tagged only `scanimport:sslyze` will not override it — use `scanimport:sslyze:weak_tls_setup` instead. Tag specificity also outranks language: a specific-tag template is used even if only a more general template has the project language.

Within the chosen tag, the plugin prefers a translation in the project's language. If several templates share that tag and language, the first match wins. If none match the language, the first matching template's main translation is used. You can maintain one template with multiple translations (recommended) or separate templates per language.

### Template Language Rendering

The plugin uses a modified Django template language with HTML comment delimiters to avoid conflicts with Markdown:

- **Variables**: `<!--{{ variable_name }}-->`
- **Control structures**: `<!--{% if condition %}-->...<!--{% endif %}-->`
- **Loops**: `<!--{% for item in items %}-->...<!--{% endfor %}-->`
- **Filters**: `<!--{{ variable|filter }}-->`

See https://docs.djangoproject.com/en/stable/ref/templates/language/ for details.

### Template Variables

Each tool provides different variables based on its output format. Check the corresponding importer source under `importers/` to see which variables are passed into the template. You can also put `<!--{% debug %}-->` in a custom template field, import a finding, and inspect the rendered Markdown preview in the frontend.

### Template Fields

Parsed finding data is applied first. Non-empty fields from the matched template then override those values.

Fields that exist in the finding data and in your project design, and that the template does not override, are kept as-is (for example `affected_components`, or `description` / `recommendation` on many importers).

You can map imported data to any fields defined in your SysReptor design, including standard fields (`title`, `summary`, `description`, `recommendation`, `cvss`) and custom fields from your project design.

### Field Mapping Example

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
