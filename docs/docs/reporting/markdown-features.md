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

```html
multiline code block
with syntax highlighting
```
~~~

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
[table caption]
```

```md linenums="1"
|             |          Grouping           ||
First Header  | Second Header | Third Header |
 ------------ | :-----------: | -----------: |
Content       |          *Long Cell*        ||
Content       |   **Cell**    |         Cell |

New section   |     More      |         Data |
And more      | With an escaped '\|'         ||  
[Prototype table]
```

## HTML Attributes
This extension allows you to set HTML attributes from markdown.

```md linenums="1"
![image](img.png){width="50%" id="img1" class="image-highlight"}

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
</>
```