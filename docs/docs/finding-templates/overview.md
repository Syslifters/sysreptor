# Templates
Templates are blueprints for findings. They contain common description texts for findings and vulnerabilities.
Describe your finding texts once in a template and reuse them in multiple pentest reports. 
When writing a report, you just have to adapt the pentest specific details and add some screenshots.


## Create a template
The template library is managed in the `Templates` section of the navigation bar.
Every user is able to view and use all templates.
Only users with the `is_template_editor` permission can create, edit and delete templates.

You can either create a new empty template by clicking "Create", or from a finding an existing report:

![Create template from finding](/images/show/template_from_finding.gif)

## Template fields
The fields available in templates are the same as in findings. 
The template field definition is created from the finding fields of all global designs and predefined finding fields (e.g. title, cvss, description, recommendation, impact, summary, etc.).

This ensures that templates are independent of designs and templates can be used in projects of any design.
Each design can define custom fields (additionally to a set of predefined fields). These custom fields are available in templates.

Some fields might not be relevant when creating templates because they are only relevant for findings in a specific design or contain project-specific settings.
You can hide these fields in the template editor to focus on the relevant fields.

![Template Fields](/images/template_fields.png)

Markdown fields allow pasting images from your clipboard:

![Paste image to markdown field](/images/show/images_in_templates.gif)