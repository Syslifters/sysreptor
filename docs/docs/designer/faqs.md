# Frequently Asked Questions

??? note "How to set solid color as page background?"

    Set background color for all pages
    ```css
    @page {
        background-color: red;
    }
    ```

    Set background color only on the first page (cover page)
    ```css
    @page:first {
        background-color: red;
    }
    ```


??? note "How to set a header background color?"

    ```css
    @page {
        --header-background-color: red;
        --header-margin-bottom: 5mm;

        @top-left-corner { 
            content: "";
            background-color: var(--header-background-color); 
            margin-bottom: var(--header-margin-bottom);
        }
        @top-center { 
            content: ""; 
            background-color: var(--header-background-color); 
            margin-bottom: var(--header-margin-bottom);
            width: 100%;
        }
        @top-right-corner { 
            content: "";
            background-color: var(--header-background-color); 
            margin-bottom: var(--header-margin-bottom); 
        }
    }
    ```

??? note "Why are my font styles (e.g. italic or bold) not working?"

    We provide some [preinstalled fonts](/designer/design-guides/#fonts) that should work out of the box.

    If you want to use custom font, make sure to [upload and include](/designer/design-guides/#custom-fonts) them in your CSS.


??? note "Why are my images or markdown not rendered in the report?"

    Your design may reference the variable incorrectly. Make sure to use this syntax:
    ```html
    <markdown :text="report.executive_summary" />
    ```

??? note "How to format links like normal text?"

    If you want all links to appear as normal text, use following CSS:
    ```css
    a {
      color: inherit;
      text-decoration: none;
      font-style: inherit;
    }
    ```

    If you want only target specific links, define a CSS class:
    ```css
    .link-none {
      color: inherit;
      text-decoration: none;
      font-style: inherit;
    }
    ```

    Then, add the defined class to your links.
    
    HTML:
    ```html
    <a href="https://www.example.com" class="link-none">https://www.example.com</a>
    ```
    Markdown:
    ```markdown
    [example.com](https://www.example.com){.link-none}
    ```


??? note "How to reference the filename in the report?"

    This is not possible, unfortunately.

    However, if you want to display your filename in your report, you might define a custom report field (or generate a dynamic filename like `report_{report.customer_name}_{report.title}.pdf`) and copy the filename from the preview to the filename textbox.


??? note "How to highlight parts of code blocks with custom style?"

    Highlighting within code-blocks works with the attribute `highlight-manual` and the marker `§§` ([see also](/reporting/markdown-features/#code-blocks)):

    ````
    ```http highlight-manual
    POST /§§important.php§§ HTTP/1.1
    ```
    ````

    To customize the hightlight style, add CSS styles for the `<mark>` tag, e.g.:
    ```
    mark {
        background-color: red;
    }
    ```

??? note "How to reduce the padding of code blocks?"

    Add following rules to CSS
    ```css
    pre code {
      padding: 0.3em !important;
    }
    ```


??? note "How to increase the space between list marker and text in lists?"

    Add following rules to CSS
    ```css
    /* Bullet list */
    ul > li {
      list-style: "\2022    ";
    }
    /* Numbered list */
    ol > li::marker {
      content: counter(list-item) ".   \200b";
    }
    ```
