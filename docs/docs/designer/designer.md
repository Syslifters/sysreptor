# Report Designer

The report designer allows you to fully customize the appearance and structure of your final PDF reports. There are no restrictions on design, ensuring that you can tailor reports to meet your specific needs.


## Getting Started

There are two main approaches to designing a report:

1. Start from an existing design
    
    Copy an existing report design (see [Demo Reports](/demo-reports.md)) and modify it to fit your requirements.

2. Start from scratch

    We recommend following approach:

    * Before starting to design, define your report fields and finding fields
    * Include base styles in CSS (`@import '/assets/global/base.css';`)
    * Define the basic report structure in the Layout editor
    * Customize the HTML and CSS to your needs via the code editors
    * Hint: Use "Preview Data" to test your design



## Report Design Components

A report design consists of the following key parts:

1. Field Definitions
  
    Field definitions determine what input fields are available in report sections and findings when writing reports (see [Field Types](/designer/field-types.md)).

    * These fields appear as form inputs in the web interface for report creation.
    * Field values can be used within Vue templates as variables for dynamic content rendering.

2. HTML + Vue.js Template
  
    The report layout is defined using the [VueJS template language](https://vuejs.org/guide/essentials/template-syntax.html){target=_blank}, which is an extension of standard HTML and JavaScript.
  
    * HTML structure defines the layout of the report.
    * Vue.js enables dynamic content generation by using variables, loops, and conditions.

3. CSS Styles
  
    CSS is used to style the report for PDF output.


## Vue.js Template Basics

Here are some essential Vue.js template features for report design:

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

For more details and advanced features see the [VueJS documentation](https://vuejs.org/guide/essentials/template-syntax.html){target="_blak"}


## Predefined Components

Predefined components are ready-to-use HTML+CSS snippets that help streamline the report design process. 
They provide commonly used report elements (e.g. cover page, page header/footer, table of contents, findings list, appendix, etc.) that can be easily customized to fit specific needs.
They serve as a starting point when initially creating report designs.

Predefined components can be added via drag-and-drop in the desing editor's "Layout" tab.
When adding, the HTML and CSS code predefined components is inserted in the design's HTML and CSS editor.
This code can be customized afterwards.

