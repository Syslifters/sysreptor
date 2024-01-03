# Design Guides
We provide many useful default styles in our `base.css`. You can import them to your report's CSS using:

```css
@import "/assets/global/base.css"
```

If you want to customize the styles (like fonts, code blocks, etc.), have a look at the following chapters.

!!! tip "Use the following snippets as a guide how to override the base styles."

    You do not need them, if you imported the base styles and don't need further customization.


## Headings
```css
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

```css
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
```css
html {
  overflow-wrap: break-word;
}
```

## Justified texts
```css
p {
  text-align: justify;
  text-align-last: start;
}
```

## Lists
Style list marker separately with `::marker`
```css
li::marker {
  color: red;
}
```

## Fonts
Fonts can be used in elements with the CSS rule `font-family`.

Following example uses two fonts for the document: 
`Roboto` for regular text (set for the whole `html` document) and 
the monospace font `Source Code Pro` for `code` blocks.

```css
html {
  font-family: "Noto Sans", sans-serif;
  font-size: 10pt;
}

code {
  font-family: "Noto Sans Mono", monospace;
}
```

We provide a range of fonts ready to use. Following fonts are available:

* [Noto Sans](https://fonts.google.com/noto/specimen/Noto+Sans){target=_blank}
* [Noto Serif](https://fonts.google.com/noto/specimen/Noto+Serif){target=_blank}
* [Open Sans](https://fonts.google.com/specimen/Open+Sans){target=_blank} - similar to Arial
* [Roboto Flex](https://fonts.google.com/specimen/Roboto+Flex){target=_blank}
* [Roboto Serif](https://fonts.google.com/specimen/Roboto+Serif){target=_blank}
* [STIX Two Text](https://fonts.google.com/specimen/STIX+Two+Text){target=_blank} - similar to Times New Roman
* [Arimo](https://fonts.google.com/specimen/Arimo){target=_blank} - similar to Verdana
* [Exo](https://fonts.google.com/specimen/Exo){target=_blank}
* ~~[Lato](https://fonts.google.com/specimen/Lato){target=_blank}~~*
* ~~[Roboto](https://fonts.google.com/specimen/Roboto){target=_blank}~~*
* ~~[Tinos](https://fonts.google.com/specimen/Tinos){target=_blank}~~*


Monospace fonts (for code blocks):

* [Roboto Mono](https://fonts.google.com/specimen/Roboto+Mono){target=_blank}
* [Noto Sans Mono](https://fonts.google.com/noto/specimen/Noto+Sans+Mono){target=_blank}
* [Source Code Pro](https://fonts.google.com/specimen/Source+Sans+Pro){target=_blank}
* [Red Hat Mono](https://fonts.google.com/specimen/Red+Hat+Mono){target=_blank}
* ~~[Courier Prime](https://fonts.google.com/specimen/Courier+Prime){target=_blank}~~*

*Deprecated, replaced by similar-looking fonts

### Custom Fonts
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
