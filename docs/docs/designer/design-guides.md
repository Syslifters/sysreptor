# Design Guides
## Headings
```css linenums="1"
/* Avoid page breaks in headlines */
h1, h2, h3, h4, h5, h6 {
  page-break-inside: avoid;
  page-break-after: avoid;
}
```

## Code
* `code`: code block and inline code
* `pre code`: code block
* `.code-block`: code block rendered from markdown
* `.code-inline`: inline code rendered from markdown

```css linenums="1"
pre code {
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
To set a global font set `font-family` for the `html` tag. 

```css linenums="1"
html {
  font-family: Arial, Helvetica, sans-serif;
  font-size: 10pt;
}
```

## Custom Fonts
Custom fonts can be added with CSS `@font-face` rules.
Requests to external systems are blocked. 
Therefore you have to upload font files as assets and include them with their relative asset URL starting with `/asset/name/<filename>`.

For google fonts you can generate the font files with this tool: https://google-webfonts-helper.herokuapp.com/fonts/exo?subsets=latin
This generates all CSS rules and provides font files for download.

It is possible to upload the font-face CSS rules in a separate file and include it in the main stylesheet with their asset URLs.

