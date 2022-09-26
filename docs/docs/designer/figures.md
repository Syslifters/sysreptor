# Figures

## Markdown images
When you embed images in markdown with `![title](img.png)` the `<img>` tags are wrapped in `<figure>` tags. 
This allows to add captions with `<figcaption>` tags.

It is recommended that you also use `<figure>` tags when placing images in your HTML template in text.
Except for logos in headers or background images on the title page.

```html linenums="1"
<figure>
  <img src="...">
  <figcaption>Caption</figcaption>
</figure>
```

### Image width
```md linenums="1"
![Image with half the page width](img.png){width="50%"}
![Exactly sized image](img.png){width="10cm" height="7cm"}
```

### Two images side by side
**TODO**: support inline images; maybe find/implement a markdown-only without the requirement for extra CSS classes

## Basic styling
```css linenums="1"
/* Image styling */
/* Prevent images from overflowing figure or page width */
img {
    max-width: 100%;
}
figure {
    page-break-inside: avoid;
    text-align: center;
    margin-left: 0;
    margin-right: 0;
}
figcaption {
    font-weight: bold;
    page-break-before: avoid;
}
```


## Figure numbering 
```css linenums="1"
html {
  counter-reset: figure-counter;
}

figcaption::before {
    counter-increment: figure-counter;
    content: "Figure " counter(figure-counter) ": ";
}
```


## List of Figures

### Template Component
Works similar like table of contents.
The component uses multi-pass rendering.
In the first render-pass it does nothing, in the second pass it collects all previously rendered `<figcaption>` tags and provides them in the variable `items`.

```html linenums="1"
<list-of-figures v-slot="items">
  <section v-if="items.length > 0">
    <h1 class="in-toc">List of Figures</h1>
    <ul class="lof">
      <template v-for="item in items">
        <li>
          <a :href="item.href">{{ item.title }}</a>
        </li>
      </template>
    </ul>
  </section>
  <pagebreak />
</list-of-figures>
```

### Referencing figure numbers
```css linenums="1"
.lof {
    padding-left: 0;
}
.lof li {
    list-style: none;
    padding-left: 0;
}
.lof li a {
    color: black;
    text-decoration: none;
}
.lof a::before {
    content: "Figure " target-counter(attr(href), figure-counter) " - ";
}
.lof a::after {
    content: " " leader(".") " " target-counter(attr(href), page);
}
```

