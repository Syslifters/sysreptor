# Figures

## Markdown images
When you embed images in markdown with `![title](img.png)` the `<img>` tags are wrapped in `<figure>` tags. 
This allows to add captions with `<figcaption>` tags.

It is recommended that you also use `<figure>` tags when placing images in your HTML template in text.
Except for logos in headers or background images on the title page.

```html
<figure>
  <img src="...">
  <figcaption>Caption</figcaption>
</figure>
```

### Image width
```md
![Image with half the page width](img.png){width="50%"}
![Exactly sized image](img.png){width="10cm" height="7cm"}
```

<!--
### Two images side by side
TODO: support inline images; maybe find/implement a markdown-only without the requirement for extra CSS classes
-->

## Basic styling
```css
/* Image styling */
/* Prevent images from overflowing figure or page width */
img {
    max-width: 100%;
}
figure {
    break-inside: avoid;
    text-align: center;
    margin-left: 0;
    margin-right: 0;
}
figcaption {
    font-weight: bold;
    break-before: avoid;
}
```


## Figure numbering 
```css
html {
  counter-reset: figure-counter;
}

figure:has(figcaption) {
    counter-increment: figure-counter;
    content: "Figure " counter(figure-counter) ": ";
}
```


## List of Figures

### Template Component
Works similar like table of contents.
The component uses multi-pass rendering.
In the first render-pass it does nothing, in the second pass it collects all previously rendered `<figcaption>` tags and provides them in the variable `items`.

```html
<list-of-figures id="lof" v-slot="items" >
    <section v-if="items.length > 0">
        <h1 class="in-toc">List of Figures</h1>
        <ul>
            <li v-for="item in items">
                <ref :to="item.id" />
            </li>
        </ul>
    </section>
    <pagebreak />
</list-of-figures>
```

### Referencing figure numbers
```css
#lof li {
    list-style: none;
    margin: 0;
    padding: 0;
}
#lof .ref-figure::before {
    content: var(--prefix-figure) target-counter(attr(href), figure-counter) " - ";
}
#lof .ref-figure > .ref-title {
    display: inline;
}
#lof .ref-figure::after {
    content: " " leader(".") " " target-counter(attr(href), page);
}
```

