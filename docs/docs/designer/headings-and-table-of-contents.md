# Headings and Table of Contents
We provide many useful default styles in our `base.css`. You can import them to your report's CSS using:

```css
@import "/assets/global/base.css"
```

Headings and Table of Contents can be used out of the box with the imported styles.  
If you want to customize heading numberings or table of content (like margins, etc.), have a look at the following chapters.

## Customization

!!! tip "Use the following snippets as a guide how to override the base styles."

    You do not need them, if you imported the base styles and don't need further customization.


CSS has counters to automatically number items such as headings, figures, etc. and also generate table of contents and list of figures with these numbers.

This allows you to automatically produce a structure similar to
```md
1 Heading
1.1 Subheading
1.2 Subheading
1.2.1 Subsubheading
2 Heading
A Appendix
A.1 Appendix Subheading
```

Additional resources:

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

```css
html {
  /* Define counters and reset them */
  counter-reset: h1-counter h2-counter h3-counter;
}

/* Heading numbers 
Usage in HTML: 
  <h1 class="numbered">Heading</h1> => 1 Heading 
  <h2 class="numbered">Subheading</h2> => 1.1 Subheading
*/
h1.numbered::before {
    padding-right: 5mm;
    counter-increment: h1-counter;
    content: counter(h1-counter);
}
h2.numbered::before{
    padding-right: 5mm;
    counter-increment: h2-counter;
    content: counter(h1-counter) "." counter(h2-counter);
}
h3.numbered::before{
    padding-right: 5mm;
    counter-increment: h3-counter;
    content: counter(h1-counter) "." counter(h2-counter) "." counter(h3-counter);
}

/* Reset counters of sub-headings below the current level */
h1.numbered {
    counter-reset: h2-counter h3-counter;
}
h2.numbered {
    counter-reset: h3-counter;
}
```

### Appendix Numbering
If you want appendix sections that are numbered differently, an additional counter can be used that uses a different number formatting.
E.g. with A, A.1, A.2, B, B.1, etc. instead contiuned numbering 4, 4.1, 4.2, 5, 5.1, etc.

CSS counters can specify a counter style to use such as `upper-alpha` instead of decimal numbers.

```css
html {
  /* NOTE: only one html {} block with counter-reset rules should exist; if there exist multiple, they overwrite each other */
  counter-reset: h1-counter h2-counter h3-counter h1-appendix-counter;
}

/* Appendix heading numbers
Usage in HTML: 
<section class="appendix">
  <h1 class="numbered">Heading</h1> => A Heading 
  <h2 class="numbered">Subheading</h2> => A.1 Subheading
</section>
*/
.appendix h1.numbered::before {
    padding-right: 5mm;
    counter-increment: h1-appendix-counter;
    content: counter(h1-appendix-counter, upper-alpha);
}
.appendix h2.numbered::before {
    padding-right: 5mm;
    counter-increment: h2-counter;
    content: counter(h1-appendix-counter, upper-alpha) "." counter(h2-counter);
}
.appendix h3.numbered::before{
    padding-right: 5mm;
    counter-increment: h3-counter;
    content: counter(h1-appendix-counter, upper-alpha) "." counter(h2-counter) "." counter(h3-counter);
}

/* Reset counters of sub-headings below the current level */
.appendix h1.numbered {
    counter-reset: h2-counter h3-counter;
}
.appendix h2.numbered {
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

All HTML attributes of the target element are collected and passed to `<table-of-contents>`.
This can be used to e.g. determine if an item is in an appendix section or regular chapter.


### Table of Contents Example
This example renders a table of contents with

* heading number (via CSS counters)
* heading title
* a leader (line of dots between title and page number)
* page number
* links entries to the target pages, such that you can click on the TOC entries and jump to the referenced page
* supports regular chapters and appendix chapters

```html
<table-of-contents id="toc" v-slot="{ items: tocItems }">
  <h1>Table of Contents</h1>
  <ul>
    <li v-for="item in tocItems" :class="'toc-level' + item.level">
      <ref :to="item.id" />
    </li>
  </ul>
  <pagebreak />
</table-of-contents>
```

```css
#toc li {
  list-style: none;
  margin: 0;
  padding: 0;
}
#toc .ref::before {
    padding-right: 0.5em;
}
#toc .ref::after {
    content: " " leader(".") " " target-counter(attr(href), page);
}
#toc .toc-level1 {
  font-size: 1.5rem;
  font-weight: bold;
  margin-top: 0.8rem;
}
#toc .toc-level2 {
  font-size: 1.2rem;
  font-weight: bold;
  margin-top: 0.5rem;
  margin-left: 2rem;
}
#toc .toc-level3 {
  font-size: 1rem;
  margin-top: 0.4rem;
  margin-left: 4rem;
}
#toc .toc-level4 {
  font-size: 1rem;
  margin-top: 0;
  margin-left: 6rem;
}
```

### Include items in TOC
```html
<h1 class="in-toc">Table of Contents</h1> <!-- note the missing class "numbered" -->
<h1 class="in-toc numbered">Section 1</h1>
<h2 class="in-toc numbered">Subsection 1.1</h2>
<h2 class="in-toc numbered">Subsubsection 1.1.1</h2>
<h1 class="numbered">Section 2: Not in TOC</h1>
<section class="appendix">
    <h1 class="in-toc numbered">Appendix A</h1>
    <h2 class="in-toc numbered">Appendix A.1</h2>
</section>
```


### Referencing sections in text (outside of TOC)
Headings can not only be referenced in the table of contents, but anywhere in the document.
References can be added via an `<a>` tag that links to the `id` of an heading element. In HTML (and markdown), a `<ref>` helper component is used to generate the `a` tag with corresponding CSS classes for referencing.

See [References](../reporting/references.md) for examples how to reference items.


```css
/* Hide section title (show only number) e.g. "1.1" */
.ref-heading .ref-title { 
  display: none;;
}
#toc .ref-heading .ref-title {
  display: initial;
}

/* Reference chapter title */
.chapter-ref-title::before {
    content: "Chapter " target-text(attr(href));
}
```
