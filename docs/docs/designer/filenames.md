# Filename

Configure the filename used when downloading the rendered PDF report by setting a custom filename through HTML meta tags in your design template. This allows for dynamic, context-aware filenames based on report data.

The filename is set using a `<meta>` tag with the name `sysreptor-filename`. Use Vue's `<teleport>` component to inject this meta tag into the document head, and leverage Vue's template syntax to create dynamic filenames from report data, JavaScript expressions, and formatting utilities. All report fields are accessible via the `report` object. The filename should end with `.pdf`.

```html
<teleport to="head">
  <meta 
    name="sysreptor-filename" 
    :content="`pentest_report_${report.title.replaceAll(/\s+/g, '_')}_${report.report_date}.pdf`" 
  />
</teleport>
```

