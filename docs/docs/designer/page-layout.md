# Page Layout

## Page size
Set the page margin such that all regular content fits in the page and there is enough space on the page borders for headers and footers.
Page headers and footers should be inside the margin box to not overlap with text content.

```css linenums="1"
@page {
  size: A4 portrait;
  margin: 35mm 20mm 25mm 20mm;
}
```

## Headers and Footers
Headers and footers are placed inside the page margin box (outside the regular page content).
To display headers and footers at a fixed position on every page use `position: running(header)` in combination with `content: element(header)`.

See:

* https://printcss.net/articles/running-headers-and-footers { target=_blank }
* https://www.w3.org/TR/css-gcpm-3/#running-syntax { target=_blank }

```css linenums="1"
@page {
  @top-right {
    content: element(header-right);
  }
}
#header {
  position: running(header-right);
}
#header img {
  height: 2cm;
}
```

```html linenums="1"
<div id="header">
  Text or 
  <img src="logo.png" alt="logo">
</div>
```

### Hide headers on title page
Headers and footers are also rendered on the title page by default.
To hide them, override `content` containing the `element(header)` on the first page.

```css linenums="1"
@page :first {
  @top-right {
    content: "";
  }
}
```



## Page numbers
The page number is a built-in CSS counter that can be used in `content`.
```css linenums="1"
/* Add page number at the bottom right corner of pages */
@page {
  @bottom-right-corner {
    content: counter(page) " / " counter(pages);
  }
}

/* Don't show page number on the title page */
@page :first {
  @bottom-right-corner {
    content: "";
  }
}
```

Page numbers can also be placed in footers together with additonal elements (see above). 
The page counter then has to be used in a pseudo element such as `::before` or `::after`.



## Pagebreaks
The easiest way to add a pagebreak is to include a `<pagebreak />` component in the HTML template.

In CSS page breaks can be controlled with 
```css linenums="1"
.selector {
  page-break-before: always;
  page-break-inside: avoid;
  page-break-after: always;
}
```

## Front Page Styling
The title page often is very different from the rest of the report,
because it has no continuous text.
Often, it contains the report title, a pretty background image and 
text blocks placed on specific locations not following any continuous text flow.

It is best to place element at specific offsets using `position: absolute` in combination with `top/bottom` and `left/right`.

You may also want to disable headers and footers on the title page (described above).

```css linenums="1"
#page-cover {
  /* Use the full page; overlay page margin box */
  margin: -35mm -20mm 26mm -20mm;
}
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
