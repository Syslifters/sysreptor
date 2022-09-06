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

```html
<p>{{ formatDate(report.report_date) }}</p>
<p>{{ formatDate(report.report_date, 'iso') }}</p>
<p>{{ formatDate(report.report_date, 'medium') }}</p>
<p>{{ formatDate(report.report_date, {year: 'numeric', month: 'long', day: '2-digit'}, 'de-DE') }}</p>
```

