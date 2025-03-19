# Tables
## Basic Table Styling
```css
table {
  width: 100%;
  caption-side: bottom;
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


## List of Tables
Works similar like table of contents.
The component uses multi-pass rendering.
In the first render-pass it does nothing, in the second pass it collects all previously rendered `<caption>` tags and provides them in the variable `items`.

```html
<list-of-tables v-slot="{slotDataSyntax}">
  <section v-if="tables">
    <h1 id="lot" class="in-toc">List of Tables</h1>
    <ul>
      <li v-for="table in tables">
        <ref :to="table.id" />
      </li>
    </ul>
    <pagebreak />
  </section>
</list-of-tables>
```
 
```css
#lot li {
  list-style: none;
  margin: 0;
  padding: 0;
}
#lot .ref {
  color: black;
  text-decoration: none;
}
#lot .ref-table::before {
  content: "Table " target-counter(attr(href), table-counter) " - ";
}
#lot .ref-table::after {
  content: " " leader(".") " " target-counter(attr(href), page);
}
```

