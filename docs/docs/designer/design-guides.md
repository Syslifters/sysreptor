# Design Guides
## Headings
```css linenums="1"
/* Avoid page breaks in headlines */
h1, h2, h3, h4, h5, h6 {
  break-inside: avoid;
  break-after: avoid;
}
```

## Code
* `code`: code block and inline code
* `pre code`: code block
* `.code-block`: code block rendered from markdown
* `.code-inline`: inline code rendered from markdown

```css linenums="1"
pre code {
  display: block !important;
  border: 1px solid black;
  padding: 0.2em;
}
code {
    background-color: whitesmoke;
}

/* Allow line wrapping in code blocks: prevent code from overflowing page */
pre {
  white-space: pre-wrap;
}
```

## Prevent page overflow of long texts
```css linenums="1"
html {
  overflow-wrap: break-word;
}
```

## Justified texts
```css linenums="1"
p {
  text-align: justify;
  text-align-last: auto;
}
```

## Lists
Style list marker separately with `::marker`
```css linenums="1"
li::marker {
  color: red;
}
```

# Fonts
Fonts can be used in elements with the CSS rule `font-family`.

Following example uses two fonts for the document: 
`Roboto` for regular text (set for the whole `html` document) and 
the monospace font `Source Code Pro` for `code` blocks.

```css linenums="1"
html {
  font-family: "Noto Sans", sans-serif;
  font-size: 10pt;
}

code {
  font-family: "Noto Sans Mono", monospace;
}
```

We provide a range of fonts ready to use. Following fonts are available:
* [Open Sans](https://fonts.google.com/specimen/Open+Sans){target=_blank} - similar to Arial
* [Noto Sans](https://fonts.google.com/noto/specimen/Noto+Sans){target=_blank}
* [Noto Serif](https://fonts.google.com/noto/specimen/Noto+Serif){target=_blank}
* [Exo](https://fonts.google.com/specimen/Exo){target=_blank}
* [Lato](https://fonts.google.com/specimen/Lato){target=_blank}
* [Roboto](https://fonts.google.com/specimen/Roboto){target=_blank}
* [Roboto Serif](https://fonts.google.com/specimen/Roboto+Serif){target=_blank}
* [Tinos](https://fonts.google.com/specimen/Tinos){target=_blank} - simliar to Times New Roman


Monospcae fonts (for code blocks):
* [Roboto Mono](https://fonts.google.com/specimen/Roboto+Mono){target=_blank} - monospace
* [Noto Sans Mono](https://fonts.google.com/noto/specimen/Noto+Sans+Mono){target=_blank} - monospace
* [Source Code Pro](https://fonts.google.com/specimen/Source+Sans+Pro){target=_blank} - monospace
* [Courier Prime](https://fonts.google.com/specimen/Courier+Prime){target=_blank} - monospace, similar to Courier New


## Custom Fonts
Custom fonts can be added with CSS `@font-face` rules.
Requests to external systems are blocked. 
Therefore you have to upload font files as assets and include them with their relative asset URL starting with `/asset/name/<filename>`.

For google fonts you can generate the font files with this tool: https://google-webfonts-helper.herokuapp.com/fonts/
This generates all CSS rules and provides font files for download.

It is possible to upload the `@font-face` CSS rules in a separate file and include it in the main stylesheet with their asset URLs.

```css
@font-face {
  font-family: 'Roboto';
  font-weight: 400;
  src: url('/assets/name/roboto-regular.woff2')
}
```
