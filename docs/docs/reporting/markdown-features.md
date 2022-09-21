# Markdown Features
The markdown syntax used in this project is based on the [CommonMark spec](https://spec.commonmark.org/){ target=_blank} with some extensions.

This document briefly describes the most important markdown syntax.
Non-standard markdown syntax is described more detailed.

## Common Markdown
~~~md linenums="1"
# Heading h1
## Heading h2
### Heading h3
#### Heading h4

Inline text styling: **bold**, _italic_, ~~strikethrough~~, `code`

Links: [Example Link](https://example.com)

* list
* items
  * nested list

1. numbered
2. list

```bash
echo "muliline code block";
# with syntax highlighting
```
~~~

## Underline
Underline is not supported in markdown. However you can insert HTML `<u>` tags to underline text.

```md linenums="1"
Text with <u>underlined</u> content.
```

## Images
Images use the standard markdown syntax, but are rendered as figures with captions.

```md linenums="1"
![Figure Caption](img.png){width="50%"}

![caption _with_ **markdown** `code`](img.png)
```

``` html linenums="1"
<figure>
  <img src="https://example.com/img.png" style="width: 50%">
  <figcaption>Figure Caption</figcaption>
</figure>
```

## Footnotes
```md linenums="1"
Text text^[footnote content] text.
```


## Tables
For tables the [MultiMarkdown syntax](https://fletcher.github.io/MultiMarkdown-6/syntax/tables.html){ target=_blank} is used.
This syntax supports table captions, grouping rows rows and cols to span multiple cells.

```md linenums="1"
| table | header |
| ------- | --------- |
| cell    | value   |

: table caption
```

## HTML Attributes
This extension allows you to set HTML attributes from markdown.
Place attributes in curly braces directly after the targeted element (without spaces between). 
Attributes are key value pairs (`attr-name="attr-value"`)
Shortcuts for setting the attribute `id` (`#id-value`) and `class` (`.class-value`) are supported.

```md linenums="1"
![image](img.png){#img-id .image-class1 .image-class2 width="50%"}

Text with [styled link](https://example.com/){class="link-class" style="color: red"} in it.
```

## Inline HTML
If something is not possible with markdown, you can fall back to writing HTML code and embed it in the markdown document.

```md linenums="1"
Text *with* **markdown** `code`.

<figure class="figure-side-by-side">
  <img src="img1.png" />
  <img src="img2.png" />
  <figcaption>Two images side-by-side</figcaption>
</figure>
```
