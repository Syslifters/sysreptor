# Tables
## Basic Table Styling
```css
table {
  width: 100%;
  caption-side: bottom;
}
/* Avoid page breaks inside table rows */
tr {
  break-inside: avoid;
}

/* Table borders */
table, th, td {
  border: 1px solid black;
  border-collapse: collapse;
}
/* Bold table headings */
th {
  font-weight: bold;
}
/* Table caption */
table caption {
  font-weight: bold;
  text-align: center;
}
```


## Complex Tables
See: https://www.w3.org/WAI/tutorials/tables/irregular/

**TLDR**:

* Header spanning multiple columns: `<th colspan="3">`
* Header spanning multiple rows: `<th rowspan="3" scope="rowgroup">`

### Vertial Text in Row headers
Rotate text with `transform`.

```html
<table>
  <caption>Complex table with vertical text spanning multiple rows</caption>
  <tr>
    <th rowspan="3" scope="rowgroup" class="rowheader-vertical">
      <p><span>Vertical Text</span></p>
    </th>
    <th colspan="2">Horizontal Text</th>
  </tr>
  <!-- rows -->
</table>
```

```css
.rowheader-vertical {
    width: 2em;
}
.rowheader-vertical p {
    white-space: nowrap;
    overflow: visible;
    width: 2em;
    margin-left: 0.5em;
}
.rowheader-vertical p span {
    display: inline-block;
    transform: translateX(-50%) rotate(270deg) translateY(50%);
}
```


## Table numbering
```css
html {
  counter-reset: table-counter;
}

table:has(caption) {
    counter-increment: table-counter;
}
caption::before {
  content: "Table " counter(table-counter) " - ";
}
```

## List of Tables
### Template Component
Works similar like table of contents.
The component uses multi-pass rendering.
In the first render-pass it does nothing, in the second pass it collects all previously rendered `<caption>` tags and provides them in the variable `items`.

```html
<list-of-tables v-slot="{ items }">
  <section v-if="items.length > 0">
    <h1 class="in-toc">List of Tables</h1>
    <ul class="lot">
      <template v-for="item in items">
        <li>
          <a :href="item.href">{{ item.title }}</a>
        </li>
      </template>
    </ul>
  </section>
  <pagebreak />
</list-of-tables>
```

### Referencing figure numbers
```css
.lot {
    padding-left: 0;
}
.lot li {
    list-style: none;
    padding-left: 0;
}
.lot li a {
    color: black;
    text-decoration: none;
}
.lot a::before {
    content: "Table " target-counter(attr(href), table-counter) " - ";
}
.lot a::after {
    content: " " leader(".") " " target-counter(attr(href), page);
}
```

