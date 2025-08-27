# Render Sections Plugins

This plugin allows you to create selectable sections to render to a PDF without rendering the whole report. 
It is possible to render multiple sections in one PDF and to render each section to a separate PDF.

The plugin is closely related to the `renderfindings` plugin (it is based on the original code), but extends it to support choosing arbitrary parts of your report.


## Configuration

```
ENABLED_PLUGINS="rendersections"
```

You will need to update your design to support this plugin, as it relies on the `data-sysreptor-rendersections` attribute and an accompanying `id`.
This attribute takes one of the following values:

* `choosable`: The element can be chosen to be included or excluded from the PDF
* `related`: The element will only be included in the PDF, if one of the related sections is included. This is based on the attribute `data-sysreptor-rendersections-relatedids`, which takes a `,` separated list of section IDs.

Compared to the `renderfindings` plugin, this works also on non-top-level elements and only affects elements with the attribute `data-sysreptor-rendersections`.

How rendering works:

* Select one or multiple sections to render
    * When getting the list of possible sections, the report HTML is fully rendered once and all items with the attribute `data-sysreptor-rendersections` and an `id` set are listed.
    * The name for each section that is used in the list can be overriden by setting the attribute `data-sysreptor-rendersections-name`. By default it is the element's `id`.
    * Since the report is fully rendered, you can also dynamically create elements with the attribute `data-sysreptor-rendersections` (e.g. on each of the findings, or on attachments).
* Render the selected findings and all sections to HTML using the project's design
    * The entire report is rendered to HTML with all findings/sections (this is a difference to `renderfindings`, which only includes the selected findings and therefore might have issues with graphs and references that would not be included in the report).
    * The variable `data.isPluginRenderFindings` is set to `true`. Use this variable to customize rendering. (This attribute name is kept for backwards compatibility)
* Remove non-selected sections from the HTML
    * Get all elements containing `data-sysreptor-rendersections`.
    * Remove all of these elements whose `id` is not in the list of selected sections and where there are no related findings included.
* Render post-processed HTML to PDF


## Limitations
* Different counter values than in the full report e.g. heading numbers, figures, tables, pages, etc.


## Examples

### Make Findings Choosable
```html
<section>
  <h1>Finding List</h1>
  <div v-for="finding in findings"
        :id="finding.id"
        data-sysreptor-rendersections="choosable"
        :data-sysreptor-rendersections-name="finding.title"
  >
      
    <h2>{{ finding.title }}</h2>
    ...
  </div>
</section>
```

### Related Sections
```html
<section>
  <h1>Finding List</h1>
  <div v-for="finding in findings"
      :id="finding.id"
      data-sysreptor-rendersections="choosable"
      :data-sysreptor-rendersections-name="finding.title"
  >
          
    <h2>{{ finding.title }}</h2>
    ...
  </div>
</section>

<!-- When using "related" then you don't need to set an id on the element itself, and since it's not shown as selectable in the list, a name is also not necessary -->
<section
    data-sysreptor-rendersections="related"
    :data-sysreptor-rendersections-relatedids="findings.map(x => x.id).join(',')"
>
  <h1>Finding Related</h1>
  ...
</section>
```
