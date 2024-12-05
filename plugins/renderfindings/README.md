# Export Findings Plugins

This plugin exports single findings to a PDF without rendering the whole report. 


## Configuration

```
ENABLED_PLUGINS="renderfindings"
```

You might need to update your design to support this plugin.
This plugin depends on some conventions in the design to work properly.
* Findings need to have a `:id="finding.id"` attribute (e.g. on `<h2>` finding title or wrapper `<div>`)
* Top-level elements containing elements with attribute `data-sysreptor-renderfindings="include"` will be included in the PDF
* Elements with attribute `data-sysreptor-renderfindings="exclude"` will be removed from the PDF
* Some CSS rules might result in unexpected styling (especially `@page:first`)

How rendering works:
* Select one or multiple findings to render
* Render the selected findings and all sections to HTML using the project's design
    * Only selected findings are rendered
    * Sections are rendered, because they might affect the rendering of findings or contain data that should be included in the PDF (e.g. in headers/footers, explicitely included sections)
* Remove unnecessary sections and elements from HTML (e.g. title page, table of contents, executive summary, etc.)
    * Select all top-level elements containing findings (`:id="finding.id"`)
    * Select all top-level page headers and footers (attributes `data-sysreptor-generated="page-header"` and `data-sysreptor-generated="page-footer"`)
    * Select all top-level elements containing `data-sysreptor-renderfindings="include"` (either as attribute on top-level element or on child elements)
    * Remove all other top-level elements
    * Remove all elements with attribute `data-sysreptor-renderfindings="exclude"` (not only top-level elements, also child elements)
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

<section> <!-- the whole top-level element is included -->
  <!-- except explicitly excluded child elements -->
  <h1 data-sysreptor-renderfindings="exclude">Finding List</h1>

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

  <div data-sysreptor-renderfindings="exclude">
    <h2>Excluded</h2>
    ...
  </div>
</section>
```

### Problems involving `@page:first`
You can either include the title page by adding the attribute `data-sysreptor-renderfindings="include"` to the corresponding HTML element in your design.

```html
<section id="page-cover" data-sysreptor-generated="page-cover" data-sysreptor-renderfindings="exclude">
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

