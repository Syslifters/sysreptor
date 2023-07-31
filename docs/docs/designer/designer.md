# Report Designer

The report designer lets you customize how your final PDF reports look like.
We do not limit your report look and feel in any way and allow you to customize your reports to your needs.

A report design consists of following parts:

* Field definition
    * Defines what input fields are available in report sections and findings when writing report.
    * Fields are available as form input fields when writing reports in the web interface.
    * Field values are also available in Vue templates as variables.
* HTML+VueJS template: 
  The [VueJS template language](https://vuejs.org/guide/essentials/template-syntax.html){ target=_blank } is used for rendering HTML.
  It is based on HTML and JavaScript.
* CSS Styles: Applied to HTML for styling the PDF.


Here are basics of the Vue template language:

* Render variables with double curly braces `{{ var }}`: 
  ```html
  <h1>{{ report.title }}</h1>
  ```
* Conditional rendering with `v-if="var"` attributes: 
  ```html
  <section v-if="report.is_retest">...</section>
  <div v-if="finding.affected_components.length > 0">...</div>
  ```
* Interations with `v-for="var_item in var_list"`-loops:
  ```html
  <section v-for="finding in findings">
    <h2>Finding title: {{ finding.title }}</h2>
  </section>
  ```
* For more details and advanced features see the [VueJS documentation](https://vuejs.org/guide/essentials/template-syntax.html)

