# Footnotes

## Markdown
```md linenums="1"
Text text^[I'm a footnote [link](https://example.com)] text.
```


## Template Styling
Elements are marked as footnotes with `float: footnote`.
Footnotes use the built-in CSS counter `footnote`. It is incremented automatically.
* Styling the footnote area at the bottom of the page: `@page { @footnote { ... }}`
* Styling the footnote reference in text: `::footnote-call { ... }`
* Styling the footnote number in the footnote box at the bottom of the page: `::footnote-marker { ... }`
* Styling footnote text content (shown at the bottom of the page): same selector (and child elements) where you applied `float: footnote` (e.g. `footnote` element)

```html linenums="1"
This is a text with footnotes<footnote>I'm the footnote content</footnote> in it.
```

```css linenums="1"
/* Footnotes */
@page {
  @footnote {
    padding-top: 0.5em;
    border-top: 1px solid black;
  }
}
footnote {
  float: footnote;
}
/* Footnote number in text */
::footnote-call {
  content: counter(footnote);
}
/* Footnote number in footnote area */
::footnote-marker {
  content: counter(footnote) '.';
  display: inline-block;
  width: 2em;
  padding-right: 1em;
  text-align: right;
}
/* Styling links in footnotes */
footnote a {
  color: black;
  text-decoration: none;
}
```

