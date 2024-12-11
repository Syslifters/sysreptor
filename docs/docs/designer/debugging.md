# Debugging
## Template Data Debugging
JSON data of reports is available in templates for rendering.
The structure of this data depends on your defined report and finding fields, i.e. it may be different for each Design.

You can view the current data structure by dumping it in the PDF.

```html
<h1>All available data</h1>
<pre>{{ data }}</pre>

<h1>Report</h1>
<pre>{{ report }}</pre>

<h1>Findings</h1>
<pre>{{ findings }}</h1>
```

## CSS Debugging
There is no way to interactively debug CSS rules.
The PDFs are rendered statically and returned as a file. 
There exists no interactive CSS editor like dev tools console in browsers.

However, you can set background colors or borders on elements to see where they are positioned and how big they are, e.g.

```
<div id="element-to-debug">...</div>

#element-to-debug {
  background-color: rgba(255, 0, 0, 0.2);
}
```


## Slow PDF Rendering
If you experience slow PDF rendering, here are a few tips to speed up rendering:

* Identify the slow step: Is the slow step `chromium` (Vue template to HTML) or `weasyprint` (HTML+CSS to PDF)?
* If `weasyprint` is slow (most likely):
    * Weasyprint render times increase with the number of pages and the complexity of the HTML/CSS. Rendering times up to 20s are normal for complex reports.
    * Table rendering is a common bottleneck, especially with large tables containing multiline cells with `table-layout: auto` (default). Try settings `table-layout: fixed;` in your design's CSS and assign fixed widths to columns.
    ```css
    table { 
      table-layout: fixed; 
    }
    .markdown table { 
      /* Keep auto layout for markdown tables to not cause unexpected rendering, 
      because we can't control the column widths in the design */
      table-layout: auto; 
    }  
    ```
    ```html
    <table>
      <thead>
        <tr>
          <!-- Set widths in table header -->
          <th style="width: 8em;">Column 1</th>
          <th style="width: auto;">Column 2</th>
        </tr>
      </thead>
      <tbody>...</tbody>
    </table>

    <table>
      <!-- Set widths in colgroup. Required when cells in table header span 
      multiple columns or when no table header is included. -->
      <colgroup>
        <col style="width: 8em;">
        <col style="width: auto;">
      </colgroup>
      <thead>
        <tr>
          <th colspan="2">Column 1</th>
        </tr>
      </thead>
      <tbody>...</tbody>
    </table>
    ```
    * If that did not help, try to identify the slowest part by commenting out HTML and CSS blocks until rendering is fast again. Try to optimize the slow part, by using different CSS rules or HTML structures.
* If `chromium` is slow:
    * Chromium has rendering times of up to 5s for complex reports. This step is usually faster than `weasyprint`.
    * If this step is slow, try to identify the slowest part by commenting out Vue template blocks (e.g. custom JS functions) until rendering is fast again. Try to optimize the slow part, by using different Vue template structures.

