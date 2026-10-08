# Optional chapters

These snippets show a chapter only when the project includes that type of test. Copy the snippet you need into your own design.

The helper sits in a hidden block at the top of the HTML. `v-show="false"` runs the assignment and keeps the block out of the PDF. See [Helper functions and variables](/designer/formatting-utils#helper-functions-and-variables).


## Chapters for each test type

Add a field `test_types` whose type is a list and the items are [enums](/designer/field-types#enum). Each choice is one type of test. An internal test, an external test, and a web test are examples. The same structure fits any set of types you define. The choice `value` is the id used in `hasTestType`. Writers select one type or several on the project.

```html
<div v-show="false">
  {{ hasTestType = function (type) {
    return (report.test_types || []).some(item => item.value === type);
  } }}
</div>
```

```html
<section v-if="hasTestType('web_pentest')">
  <h1 id="web-pentest" class="in-toc">Web pentest</h1>
  <p>Standard wording for web pentests.</p>
  <pagebreak />
</section>
```

`web_pentest` is one enum value. Repeat the section for each type, with its own `v-if`, title, and wording. A chapter whose check is false is left out of the PDF, including its [table-of-contents](/designer/headings-and-table-of-contents) entry. The page break stays inside the `v-if`, so a type that is off does not leave an empty page.

Name the selected types in one sentence. [`<comma-and-join>`](/designer/formatting-utils#text-enumeration-formatting) inserts the separators. Put the phrase for each type in the template, and show it only when that type is selected:

```html
<p v-if="hasTestType('web_pentest') || hasTestType('external_pentest')">
  During this assessment we performed
  <comma-and-join>
    <template #web_pentest v-if="hasTestType('web_pentest')">a web pentest</template>
    <template #external_pentest v-if="hasTestType('external_pentest')">an external pentest</template>
  </comma-and-join>.
</p>
```

One phrase is printed alone. Two phrases are joined with `and`. The paragraph is omitted when neither type is selected.

* `web_pentest`: `During this assessment we performed a web pentest.`
* `web_pentest` and `external_pentest`: `During this assessment we performed a web pentest and an external pentest.`

For a few types, boolean fields such as `include_web_pentest` work as well. The helper then reads the matching field:

```html
<div v-show="false">
  {{ hasTestType = function (type) {
    return !!report['include_' + type];
  } }}
</div>
```

When every project is exactly one type, use one enum field, such as `pentest_type`, and compare its value:

```html
<section v-if="report.pentest_type.value === 'web_pentest'">
  <h1 id="web-pentest" class="in-toc">{{ report.pentest_type.label }}</h1>
</section>
```

Other optional blocks use the same `v-if` pattern. A retest report checks the boolean `is_retest`:

```html
<p v-if="report.is_retest">
  This report is a retest of findings from the previous assessment.
</p>
```
