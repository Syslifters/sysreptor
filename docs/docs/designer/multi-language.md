# Multiple languages

These snippets read the project language and translate fixed strings in the template. Copy the snippet you need into your own design.

Each helper sits in a hidden block at the top of the HTML. `v-show="false"` runs the assignments and keeps the block out of the PDF. See [Helper functions and variables](/designer/formatting-utils#helper-functions-and-variables).


## Language

The project language is selected in the project settings. It is available as `report.language` and as the `lang` attribute of the HTML document. `getLanguage()` returns that value, including a region when one is set (`de-DE`).

```html
<div v-show="false">
  {{ getLanguage = function () {
    return document.documentElement.getAttribute('lang') || report.language || 'en';
  } }}
</div>
```

Pass it to [`formatDate()`](/designer/formatting-utils#date-formatting) so the date uses that locale:

```html
{{ formatDate(report.report_date, 'long', getLanguage()) }}
```


## Translations

Fixed strings in the design, such as headings and sentences, go through `i18n`. Add a key for each string in every language. The helper uses the language part only (`de`), so `de-DE` and `de-AT` share one table. A missing language or a missing label falls back to English and emits a warning in the preview.

```html
<div v-show="false">
  {{ i18n = function (label) {
    const translations = {
      en: {
        contents: 'Contents',
        findings: 'Findings',
      },
      de: {
        contents: 'Inhalt',
        findings: 'Schwachstellen',
      },
    };
    const lang = (document.documentElement.getAttribute('lang') || report.language || 'en').split('-')[0];
    const fallback = translations.en;

    if (!translations[lang]) {
      const msg = `Language "${lang}" is not defined in the translation table`;
      console.warn(msg, { message: 'Translation not defined', details: msg });
    } else if (!(label in translations[lang])) {
      const msg = `Translation for "${label}" is not defined for language "${lang}"`;
      console.warn(msg, { message: 'Translation not defined', details: msg });
    }

    return translations[lang]?.[label] ?? fallback[label] ?? '';
  } }}
</div>
```

```html
<h1 id="contents" class="in-toc">{{ i18n('contents') }}</h1>
<h1 id="findings" class="in-toc">{{ i18n('findings') }}</h1>
```

[`<comma-and-join>`](/designer/formatting-utils#text-enumeration-formatting) takes a translated separator. Include the spaces in the translation. This block is a separate sample. In a design, add these keys to the translation table above.

```html
<div v-show="false">
  {{ i18n = function (label) {
    const translations = {
      en: {
        first: 'network',
        second: 'application',
        and: ' and '
      },
      de: {
        first: 'Netzwerk',
        second: 'Anwendung', 
        and: ' und '
      },
    };
    const lang = (document.documentElement.getAttribute('lang') || report.language || 'en').split('-')[0];
    return translations[lang]?.[label] ?? translations.en[label] ?? '';
  } }}
</div>
```

```html
<comma-and-join :and="i18n('and')">
  <template #first>{{ i18n('first') }}</template>
  <template #second>{{ i18n('second') }}</template>
</comma-and-join>
```

With two items, `<comma-and-join>` places `and` between them. The spaces are part of the translated string.

* English: `network and application`
* German: `Netzwerk und Anwendung`
