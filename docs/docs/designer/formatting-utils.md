# Formatting Utilities
Multiple utility functions for formatting are available. 

## Date Formatting
The `formatDate()` function takes three arguments:

* the date to be formatted
* (optional) format options
    * if not specified, the date is formatted as `{dateStyle: 'long'}` in the current locale of the report
    * a string for either: `iso` (format: `yyyy-mm-dd`) or `full`, `long`, `medium`, `short` date style in the current locale of the report
    * a object for [Intl.DateTimeFormat options](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/DateTimeFormat/DateTimeFormat#options){ target=_blank }
* (optional) locale to override the default locale: see [Intl.DateTimeFormat locales](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/DateTimeFormat/DateTimeFormat#locales){ target=_blank }

Examples:
```html
2022-09-21: {{ formatDate(report.report_date, 'iso') }}

21.09.22: {{ formatDate(report.report_date, 'short', 'de-DE') }}
21.09.2022: {{ formatDate(report.report_date, 'medium', 'de-DE') }}
21. September 2022: {{ formatDate(report.report_date, 'long', 'de-DE') }}
Mittwoch, 21. September 2022: {{ formatDate(report.report_date, 'full', 'de-DE') }}

9/21/22: {{ formatDate(report.report_date, 'short', 'en-US') }}
Sep 21, 2022: {{ formatDate(report.report_date, 'medium', 'en-US') }}
September 21, 2022: {{ formatDate(report.report_date, 'long', 'en-US') }}
Wednesday, September 21, 2022: {{ formatDate(report.report_date, 'full', 'en-US') }}

S 21, 22: {{ formatDate('2022-09-21', {year: '2-digit', month: 'narrow', day: '2-digit', numberingSystem: 'latn'}, 'en-US') }}
</ul>
```

## Lodash Utilities
All lodash utility functions are available in templates as `lodash`. 
See https://lodash.com/docs/ for a list of available functions.

Examples:
```html
{{ lodash.capitalize(finding.cvss.level) }}
{{ lodash.toUpper(finding.cvss.level) }}
```


## Text Enumeration Formatting
The `<comma-and-join>` template component allows joining text enumerations with commas and the last item with "and". 
Some items might be optional and not be rendered always. This component takes care of inserting separators into the text.

This example shows the basic usage for a static list of text parts. 
It renders the number of findings for each severity level. If there are no findings for a severity level, the level is omitted.
```html
<p>
  In the course of this penetration test
  <comma-and-join>
    <template #critical v-if="finding_stats.count_critical > 0"><strong class="risk-critical">{{ finding_stats.count_critical }} Critical</strong></template>
    <template #high v-if="finding_stats.count_high > 0"><strong class="risk-high">{{ finding_stats.count_high }} High</strong></template>
    <template #medium v-if="finding_stats.count_medium > 0"><strong class="risk-medium">{{ finding_stats.count_medium }} Medium</strong></template>
    <template #low v-if="finding_stats.count_low > 0"><strong class="risk-low">{{ finding_stats.count_low }} Low</strong></template>
    <template #info v-if="finding_stats.count_info > 0"><strong class="risk-info">{{ finding_stats.count_info }} Info</strong></template>
  </comma-and-join>
  vulnerabilities were identified:
</p>
```

Following example renders a dynamic list of strings from a template variable joined with commas and "and":
```html
<comma-and-join>
  <template v-for="author, authorIdx in report.authors" #[authorIdx]>{{ author }}</template>
</comma-and-join>
```

By default, `<comma-and-join>` concatenates text parts with commas and the last one with the english word "and".
These separators can be changed via the parameters `comma=", "` and `and=" and "` to format other languages.

This example joins text parts in different languages:
```html
English (default): <comma-and-join>...</comma-and-join>
English (no commas, always "and"): <comma-and-join comma=" and " and=" and ">...</comma-and-join>
German: <comma-and-join and=" und ">...</comma-and-join>
French: <comma-and-join and=" et ">...</comma-and-join>
```