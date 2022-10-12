# Referencing Sections and Findings
You can reference the headings of other sections and findings in the report, if your [design supports it](/designer/headings-and-table-of-contents/#referencing-sections-in-text-outside-of-toc).

## Reference Static Sections
```html
Detailed descriptions of findings can be found in <a href="#findings" class="chapter-ref-title"/>.

A permission to attack (see <a href="#appendix-pta" class="appendix-ref" />) was ...
```

## Reference Findings
1. Get the finding ID from the URL
    * Open the other finding that should be linked
    * Copy the last UUID from the URL ![Grab the finding ID](/images/finding_id.png)

2. Create a markdown link
    * Set the `href` to `#<copied-finding-id>` 
    * Add the previously defined CSS class `.chapter-ref-title` to automatically add the finding title in the rendered text
      ```md
      See this other finding [](#<finding-id>){.chapter-ref-title} for...
      ```
    * If you want a different text for the link, do not add the class and write the link text yourself in the square brackets
      ```md
      See this other finding [for more information](#<finding-id>)...
      ```
