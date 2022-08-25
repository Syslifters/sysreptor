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



