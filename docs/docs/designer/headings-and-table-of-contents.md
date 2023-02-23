# Headings and Table of Contents
CSS has counters to automatically number items such as headings, figures, etc. and also generate table of contents and list of figures with these numbers.

This allows you to automatically produce a structure similar to
```md linenums="1"
1 Heading
1.1 Subheading
1.2 Subheading
1.2.1 Subsubheading
2 Heading
A Appendix
A.1 Appendix Subheading
```

Additional resources:

* CSS Counters
    * https://printcss.net/articles/counter-and-cross-references
    * https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Counter_Styles/Using_CSS_counters



## Heading Numbers
This example contains code for numbering headings with pure CSS.
The heading number is placed in the `::before` pseudo-element in the DOM using CSS.

CSS counters first have to be defined with `counter-reset: <counter-name>` (best place this rule in `html`).
The counters by default start at `0`, but the start value can also be overwritten.

Before the counter value is used, it should be incremented (such that chapter numbers start at 1, not 0) with `counter-increment: <counter-name>`.
Now the counter has the correct value, we can embed it with `content: counter(<counter-name>)` in `::before` pseudo-elements.

Counters are incremented and referenced with CSS rules in selectors.
Counters have no global value at a given time, instead their values depend on the DOM-position of the elements that use them.
For example: the custom `h1-counter` is incremented at every `<h1>` tag. 
This means that between the first and the second `<h1>` tag in the DOM structure, the counter has the value `1`, 
between the second and third `<h1>` it has the value 2 and so on. 
When the CSS rule `h2::before { counter-increment: h2-counter; content: counter(h1-counter) "." counter(h1-counter); }`
accesses the counter value of `h1-counter` the value is different depending on where the targeted `h2` element is placed in the DOM.
Note that this `h2::before` rule is defined only once and applies to all `<h2>` tags.

### Basic Heading Numbering
Add numbering to heading tags which have the class `numbered`.

```css linenums="1"
html {
  /* Define counters and reset them */
  counter-reset: h1-counter h2-counter h3-counter;
}

/* Heading numbers 
Usage in HTML: 
  <h1 class="numbered">Heading</h1> => 1 Heading 
  <h2 class="numbered">Subheading</h2> => 1.1 Subheading
Manually set counter level: 
  <h1 class="numbered" data-toc-level="3">Subsubheading</h1> => 1.1.1 Subsubheading
*/
h1.numbered:not([data-toc-level])::before, .numbered[data-toc-level="1"]::before {
    padding-right: 5mm;
    counter-increment: h1-counter;
    content: counter(h1-counter);
}
h2.numbered:not([data-toc-level])::before, .numbered[data-toc-level="2"]::before{
    padding-right: 5mm;
    counter-increment: h2-counter;
    content: counter(h1-counter) "." counter(h2-counter);
}
h3.numbered:not([data-toc-level])::before, .numbered[data-toc-level="3"]::before{
    padding-right: 5mm;
    counter-increment: h3-counter;
    content: counter(h1-counter) "." counter(h2-counter) "." counter(h3-counter);
}

/* Reset counters of sub-headings below the current level */
h1.numbered:not([data-toc-level]), .numbered[data-toc-level="1"] {
    counter-reset: h2-counter h3-counter;
}
h2.numbered:not([data-toc-level]), .numbered[data-toc-level="2"] {
    counter-reset: h3-counter;
}
```

### Appendix Numbering
If you want appendix sections that are numbered differently, an additional counter can be used that uses a different number formatting.
E.g. with A, A.1, A.2, B, B.1, etc. instead contiuned numbering 4, 4.1, 4.2, 5, 5.1, etc.

CSS counters can specify a counter style to use such as `upper-alpha` instead of decimal numbers.

```css linenums="1"
html {
  /* NOTE: only one html {} block with counter-reset rules should exist; if there exist multiple, they overwrite each other */
  counter-reset: h1-counter h2-counter h3-counter h1-appendix-counter;
}

/* Appendix heading numbers
Usage in HTML: 
  <h1 class="numbered-appendix">Heading</h1> => A Heading 
  <h2 class="numbered-appendix">Subheading</h2> => A.1 Subheading
*/
h1.numbered-appendix:not([data-toc-level])::before, .numbered-appendix[data-toc-level="1"]::before {
    padding-right: 5mm;
    counter-increment: h1-appendix-counter;
    content: counter(h1-appendix-counter, upper-alpha);
}
h2.numbered-appendix:not([data-toc-level])::before, .numbered-appendix[data-toc-level="2"]::before {
    padding-right: 5mm;
    counter-increment: h2-counter;
    content: counter(h1-appendix-counter, upper-alpha) "." counter(h2-counter);
}
h3.numbered-appendix:not([data-toc-level])::before, .numbered-appendix[data-toc-level="3"]::before{
    padding-right: 5mm;
    counter-increment: h3-counter;
    content: counter(h1-counter-appendix, upper-alpha) "." counter(h2-counter) "." counter(h3-counter);
}

/* Reset counters of sub-headings below the current level */
h1.numbered-appendix:not([data-toc-level]), .numbered-appendix[data-toc-level="1"] {
    counter-reset: h2-counter h3-counter;
}
h2.numbered-appendix:not([data-toc-level]), .numbered-appendix[data-toc-level="2"] {
    counter-reset: h3-counter;
}
```



## Table of Contents
A table of contents can be included in reports via the `<table-of-contents>` component.
This component collects all elements with the class `in-toc`, and provides them as variables.
This component uses delayed multi-pass rendering to ensure that all items referenced in the TOC are already rendered and can be referenced.

### Heading Numbers in TOC
Heading numbers can be added purely with CSS using counters.
However, in order to use the correct counters, the nesting level of the heading needs to be known by CSS rules.
These cannot be determined soely in CSS.

The `<table-of-contents>` component determines the nesting level and provides this information.
`h1` to `h6` tags are assigned the correct level.
If you want to reference other elements in the TOC or overwrite the level, set it via the `data-toc-level` attribute.

All HTML attributes of the target element are collected and passed to `<table-of-contents>`.
This can be used to e.g. determine if an item is in an appendix section or regular chapter.


### Table of Contents Simple Example
This example renders a table of contents with
* heading title
* page number
* links entries to the target pages, such that you can click on the TOC entries and jump to the referenced pa

```html
<table-of-contents v-slot="tocItems">
  <ul class="toc">
    <template v-for="item in tocItems">
      <li :class="'level-' + item.level"><a :href="item.href">{{ item.title }}</a></li>
    </template>
  </ul>
</table-of-contents>
```

```css
.toc a {
    color: black;
}

.toc a::after {
    font-weight: normal;
    content: " " target-counter(attr(href), page);
    float: right;
}

.toc ul {
    list-style: none;
    padding: 0;
}

.toc .level-1 {
    margin-top: 0.7em;
    font-weight: bold;
}
.toc .level-2 {
    padding-left: 1.5em;
    margin-top: 0.35em;
    font-weight: normal;
}
.toc .level-3 {
    padding-left: 3em;
    margin-top: 0.25em;
    font-weight: normal;
}
```

### Table of Contents Complex Example
This example renders a table of contents with
* heading number (via CSS counters)
* heading title
* a leader (line of dots between title and page number)
* page number
* links entries to the target pages, such that you can click on the TOC entries and jump to the referenced page
* supports regular chapters and appendix chapters

```html
<table-of-contents v-slot="tocItems">
    <ul class="toc">
        <template v-for="item in tocItems">
            <li :class="['toc-level-' + item.level, (item.attrs.class || '').split(' ').includes('numbered') ? 'numbered' : '', (item.attrs.class || '').split(' ').includes('numbered-appendix') ? 'numbered-appendix' : '']">
                <a :href="item.href">{{ item.title }}</a>
            </li>
        </template>
    </ul>
</table-of-contents>
```

```css
.toc {
    padding-left: 0;
}
.toc a {
    color: black;
    text-decoration: none;
    font-style: inherit;
}
.toc a::after {
    content: " " leader(".") " " target-counter(attr(href), page);
}
.toc li {
    list-style: none;
    padding-left: 0;
}
.toc-level-1 {
    font-size: 14pt;
    font-weight: bold;
    margin-top: 0.8em;
}
.toc-level-1.numbered a::before {
    content: target-counter(attr(href), h1-counter);
    padding-right: 5mm;
}
.toc-level-1.numbered-appendix a::before {
    content: target-counter(attr(href), h1-appendix-counter, upper-alpha);
    padding-right: 5mm;
}

.toc-level-2 {
    font-size: 12pt;
    font-weight: bold;
    margin-top: 0.5em;
}
.toc-level-2.numbered a::before {
    content: target-counter(attr(href), h1-counter) "." target-counter(attr(href), h2-counter);
    padding-right: 5mm;
}
.toc-level-2.numbered-appendix a::before {
    content: target-counter(attr(href), h1-appendix-counter, upper-alpha) "." target-counter(attr(href), h2-counter);
    padding-right: 5mm;
}

.toc-level-3 {
    font-size: 10pt;
    margin-top: 0.4em;
}
```

### Include items in TOC
```html
<h1 class="in-toc">Table of Contents</h1> <!-- note the missing class "numbered" -->
<h1 class="in-toc numbered">Section 1</h1>
<h2 class="in-toc numbered">Subsection 1.1</h2>
<h2 class="in-toc numbered">Subsubsection 1.1.1</h2>
<h1 class="numbered">Section 2: Not in TOC</h1>
<h1 class="in-toc numbered-appendix">Appendix A</h1>
<h2 class="in-toc numbered-appendix">Appendix A.1</h2>
```


### Referencing sections in text (outside of TOC)
Headings can not only be referenced in the table of contents, but anywhere in the document.
References can be added by creating an `<a>` tag that links to the `id` of an heading element.

But there are some limitations in what you can reference: the nesting level cannot be determined automatically via CSS.
You either have to manually specify the nesting level of the referenced heading or not include the heading number in the referenced text.


```css
/* Reference chapter title */
.chapter-ref-title::before {
    content: "Chapter " target-text(attr(href));
}
/* Reference appendix with number. It is assumed that all appendix subsections are on the same nesting level */
.appendix-ref::before {
    content: "Appendix " target-counter(attr(href), h1-appendix-counter, upper-alpha) "." target-counter(attr(href), h2-counter) " " target-text(attr(href));
}
```

Example: reference static sections of the design
```html
Detailed descriptions of findings can be found in <a href="#findings" class="chapter-ref-title"/>.

A permission to attack (see <a href="#appendix-pta" class="appendix-ref" />) was ...
```

**Example:** Reference findings in markdown


1. Get the finding ID from the URL
    * Open the other finding that should be linked
    * Copy the last UUID from the URL ![Grab the finding ID](/images/finding_id.png)

2. Create a markdown link
    * Set the `href` to `#<copied-finding-id>` 
    * Add the previously defined CSS class `.chapter-ref-title` to automatically add the finding title in the rendered text
      ```md
      See this other finding [](#<finding-id>){.chapter-ref-title} for...
      ```
    * If you want a different text for the link, do not add the class and write the link text yourself in the square brackets
      ```md
      See this other finding [for more information](#<finding-id>)...
      ```
