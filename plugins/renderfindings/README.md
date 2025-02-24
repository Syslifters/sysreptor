# Render Findings Plugins

This plugin renders selected findings to a PDF without rendering the whole report. 
It is possible to render multiple findings in one PDF and to render each finding to a separate PDF.


## Configuration

```
ENABLED_PLUGINS="renderfindings"
```

You might need to update your design to support this plugin.
This plugin depends on some conventions in the design to work properly.
* Findings need to have a `:id="finding.id"` attribute (e.g. on `<h2>` finding title or wrapper `<div>`)
* The design's HTML+Vue template must not use a wapper element for the whole report, but instead use separate top-level elements for each section
* Top-level sections containing elements with attribute `data-sysreptor-renderfindings="include"` will be included in the PDF
* Detailed customization of rendered elements can be archived via `v-if="data.isPluginRenderFindings"` in design's Vue template
* Some CSS rules might result in unexpected styling (especially `@page:first`)

How rendering works:
* Select one or multiple findings to render
* Render the selected findings and all sections to HTML using the project's design
    * Only selected findings are rendered
    * Sections are rendered, because they might affect the rendering of findings or contain data that should be included in the PDF (e.g. in headers/footers, explicitely included sections)
    * The variable `data.isPluginRenderFindings` is set to `true`. Use this variable to customize rendering.
* Remove unnecessary sections and elements from HTML (e.g. title page, table of contents, executive summary, etc.)
    * Select all top-level sections containing findings (`:id="finding.id"`)
    * Select all top-level page headers and footers (attributes `data-sysreptor-generated="page-header"` and `data-sysreptor-generated="page-footer"`)
    * Select all top-level sections containing `data-sysreptor-renderfindings="include"` (either as attribute on top-level element or on child elements)
    * Remove all other top-level sections
* Render post-processed HTML to PDF


## Limitations
* Different counter values than in the full report e.g. heading numbers, figures, tables, pages, etc.
* References to other findings or sections cannot be resolved (if they are not included in the PDF)


## Examples

### Set Finding IDs
```html
<section>
  <h1>Finding List</h1>
  <div v-for="finding in findings">
    <!-- Set finding ID -->
    <h2 :id="finding.id">{{ finding.title }}</h2>
    ...
  </div>
</section>
```

### Include and Exclude Elements
```html
<section>
  <h1>Excluded</h1>
  <markdown :text="report.executive_summary" />
</section>

<section> <!-- the whole top-level section is included -->
  <!-- except explicitly excluded child elements -->
  <h1 v-if="!data.isPluginRenderFindings">Finding List</h1>

  <!-- included -->
  <div v-for="finding in findings">
    <h2 :id="finding.id">{{ finding.title }}</h2>
    ...
  </div>

  <!-- also included -->
  <div>
    ...
  </div>
</section>

<section data-sysreptor-renderfindings="include">
  <h1>Included</h1>
  ...

  <div v-if="!data.isPluginRenderFindings">
    <h2>Excluded</h2>
    ...
  </div>
</section>
```

### Problems involving `@page:first`
You can either include the title page by adding the attribute `data-sysreptor-renderfindings="include"` to the corresponding HTML element in your design.

```html
<section v-if="!data.isPluginRenderFindings" id="page-cover" data-sysreptor-generated="page-cover">
  ...
</section>
```


If you do not want to include the title page, you need to migrate `@page:first` CSS rules to named pages.

```html
<div id="header" data-sysreptor-generated="page-header">
  <div id="header-right">...</div>
</div>
<div id="footer" data-sysreptor-generated="page-footer">
  <div id="footer-left">...</div>
</div>

<section id="page-cover" data-sysreptor-generated="page-cover">
  <div class="page-cover-title">
    <h1>{{ report.title }}</h1>
    ...
  </div>
</section>
```

CSS before:
```css
@page:first {
  /* CSS rules for cover page */
  ...
}
```

CSS after:
```css
#page-cover { page: page-cover; }
@page page-cover {
  /* CSS rules for cover page */
  ...
}

#header, #footer { position: absolute; width: 0; }
```

