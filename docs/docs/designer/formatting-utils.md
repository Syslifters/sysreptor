# Formatting Utilities
Multiple utility functions for formatting are available. 

## Capitalize String
```html
<p>{{ capitalize(finding.cvss.level) }}</p>
```

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

