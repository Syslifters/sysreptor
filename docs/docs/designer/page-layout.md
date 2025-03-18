# Page Layout

## Page size
Set the page margin such that all regular content fits in the page and there is enough space on the page borders for headers and footers.
Page headers and footers should be inside the margin box to not overlap with text content.

```css
@page {
  size: A4 portrait;
  margin: 35mm 20mm 25mm 20mm;
}
```

Additional resources:

* https://printcss.net/articles/page-selectors-and-page-breaks


## Headers and Footers
Headers and footers are placed inside the page margin box (outside the regular page content).
To display headers and footers at a fixed position on every page use `position: running(header)` in combination with `content: element(header)`.

See:

* https://printcss.net/articles/running-headers-and-footers
* https://printcss.net/articles/page-margin-boxes
* https://www.w3.org/TR/css-gcpm-3/#running-syntax

```css
@page {
  @top-left {
    content: element(header-left);
  }
  @top-right {
    content: element(header-right);
  }
}
#header {
  position: absolute;
  width: 0;
}
#header #header-left { 
  position: running(header-left); 
}
#header #header-right { 
    position: running(header-right); 
    text-align: right;
}
```

```html
<div id="header" data-sysreptor-generated="page-header">
  <div id="header-left">
    <img src="/assets/name/header-logo.png" alt="logo" />
  </div>
  <div id="header-right">
    Header text
  </div>
</div>
```

## Named Pages
CSS named pages allow to define distinct styles for different pages using `@page` rules. 
By assigning a name to a page (`@page name {}`) and using `page: name;` within an element's styles, specific formatting like margins, size, orientation or headers/footers can be applied to designated sections.

Headers and footers are also rendered on the title page by default.
To hide them on specific pages, override `content` containing the `element(header)` on named pages.

```css
.page-cover {
  page: page-cover;
}
@page page-cover {
  /* Hide headers */
  @top-left { content: ""; }
  @top-right { content: ""; }
  /* Hide footers */
  @bottom-right-corner { content: ""; }
}
```

```html
<section class="page-cover">
  named page
</section>

<section>
  unnamed page: default
</section>
```



## Page numbers
The page number is a built-in CSS counter that can be used in `content`.
```css
/* Add page number at the bottom right corner of pages */
@page {
  @bottom-right-corner {
    content: counter(page) " / " counter(pages);
  }
}

/* Don't show page number on the title page */
@page page-cover {
  @bottom-right-corner { content: ""; }
}
```

Page numbers can also be placed in footers together with additonal elements (see above). 
The page counter then has to be used in a pseudo element such as `::before` or `::after`.



## Pagebreaks
The easiest way to add a pagebreak is to include a `<pagebreak />` component in the HTML template.

In CSS page breaks can be controlled with 
```css
.selector {
  break-before: always;
  break-inside: avoid;
  break-after: always;
}
```

## Front Page Styling
The title page often is very different from the rest of the report,
because it has no continuous text.
Often, it contains the report title, a pretty background image and 
text blocks placed on specific locations not following any continuous text flow.

It is best to place element at specific offsets using `position: absolute` in combination with `top/bottom` and `left/right`.

You may also want to disable headers and footers on the title page with [named pages](#named-pages).

```css
#page-cover-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 12cm;
  overflow: hidden;
}
#page-cover-background img {
  width: 100%;
}
#page-cover-title {
  position: absolute;
  top: 6cm;
  left: 4cm;
  right: 4cm;
}
```
