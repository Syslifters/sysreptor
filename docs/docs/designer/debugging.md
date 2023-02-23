# Debugging
## Template Data Debugging
JSON data of reports is available in templates for rendering.
The structure of this data depends on your defined report and finding fields, i.e. it may be different for each Design.

You can view the current data structure by dumping it in the PDF.

```html linenums="1"
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

However, you can set background colors or borders on elements to see where they are positioned and how big they are.

