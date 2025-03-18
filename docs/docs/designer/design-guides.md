# Design Guides
We provide many useful default styles in our `base.css`. You can import them to your report's CSS using:

```css
@import "/assets/global/base.css"
```

If you want to customize the styles (like fonts, code blocks, etc.), have a look at the following chapters.
You can find the content of `base.css` [here](https://github.com/Syslifters/sysreptor/blob/main/api/src/reportcreator_api/tasks/rendering/global_assets/base.css){ target="_blank" }.


!!! tip "Use the following snippets as a guide how to override the base styles."

    You do not need them, if you imported the base styles and don't need further customization.


## Headings
```css
/* Customize heading sizes */
h1 { font-size: 2rem;  }
h2 { font-size: 1.6rem; }
h3 { font-size: 1.4rem; }
h4 { font-size: 1.25rem; }
h5 { font-size: 1.1rem; }
h6 { font-size: 1rem; }
```

## Code
* `code`: code block and inline code
* `pre code`: code block
* `.code-block`: code block rendered from markdown
* `.code-inline`: inline code rendered from markdown

```css
pre code {
  border: 1px solid black;
  padding: 0.2em;
}
code {
  background-color: whitesmoke;
}
```

Code block line number information is provided for markdown code blocks, but not shown by default. Use following CSS rules to display line numbers:
```css
.code-block-line::before {
  content: attr(data-line-number);
  text-align: right;
  user-select: none;
  display: inline-block;
  width: 2em;
  margin-left: -1em;
  margin-right: 0.2em;
  padding-right: 0.3em;
  background-color: rgba(0, 0, 0, 0.1);
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

## Footnotes
```css
/* Footnote area at the bottom of the page, where the footnote text is placed */
@page {
  @footnote {
    ...  
  }
}

/* Footnote number in text */
::footnote-call {
  ...
}
/* Separator between multiple consecutive footnotes */
.footnote-call-separator {
  ...
}

/* Footnote number in footnote area */
::footnote-marker {
  ...
}

/* Styling footnote content e.g. links */
footnote a {
  color: black;
  text-decoration: none;
}
```

Additional resources:

* https://printcss.net/articles/footnotes { target=_blank }


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
