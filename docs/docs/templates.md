# Templates
Templates are blueprints for findings. They contain common description texts for findings and vulnerabilities.
Describe your finding texts once in a template and reuse them in multiple pentest reports. 
When writing a report, you just have to adapt the pentest specific details and add some screenshots.


## Create a template
The template library is managed in the `Templates` section of the navigation bar.
Every user is able to view and use all templates.
Only users with the `is_template_editor` permission can create, edit and delete templates.


## Template fields
The fields available in templates are the same as in findings. 
The template field definition is created from the finding fields of all global designs and predefined finding fields (e.g. title, cvss, description, recommendation, impact, summary, etc.).

This ensures that templates are independent of designs and templates can be used in projects of any design.
Each design can define custom fields (additionally to a set of predefined fields). These custom fields are available in templates.

Some fields might not be relevant when creating templates because they are only relevant for findings in a specific design or contain project-specific settings.
You can hide these fields in the template editor to focus on the relevant fields.

![Template Fields](/images/template_fields.png)


## Multilingual templates
Templates can contain texts for multiple languages.
This enabled you to manage all data of a template in one place even when it is translated in multiple languages. 

This is useful for pentesters in non-English speaking countries where some pentest reports are written in the native language and some in English.
Some countries also have 2, 3 or more official languages.

Each template has a (required) main language and (optionally) multiple translations.
The main language defines all fields that are required in the template (e.g. title, cvss, description, recommendation, references, etc.).
Translations can override language-specific fields (e.g. title, description, recommendation, etc.).
Fields that are not overridden are inherited from the main language (e.g. cvss, references).

This approach allows for maximum flexibility in template translations, since you can translate each field separately for each language.
Consider following scenario: 
You are writing a template in English, German and Dutch, where English is the main language and German and Dutch are translations.
In the English template you fill the text fields for title, description and recommendation with vulnerability descriptions (and some TODO markers to insert screenshots and pentest project specific details). Additionally you define the language-independent fields CVSS and references.
In the German and Dutch translations you only translate the title, description and recommendation fields need to be translated. 
The CVSS and references fields are inherited from the English template.
Let's consider you have found a great blog post describing the vulnerability in detail and want to use it as a reference in your report.
However, the blog post is only available in German, so you cannot use the for the English and Dutch template.
It is still possible to use them just for the German translation, by overriding the references field in the German translation.
The Dutch translation still inherits the English references, but the German translation contains the additional reference.


## Use templates (creating findings from templates)
When creating new findings, you can select a template to use.
The contents of template fields are copied to a new finding.

The template searchbar searches in template tags and the titles of all template translations.
For example you can search for `xss` to find all templates containing the tag `xss` or the word `xss` in the title of any translation (English, German, etc.).

![Create finding from template](/images/create_finding_from_template.png)

When selecting a template, you can select the language of the template to use.
By default the language of the pentest project is selected.
If no translation for the selected language is available, the main language of the template is used.


