# PDF Metadata

By default, SysReptor does not add any metadata to rendered PDFs.
Metadata is only written when you define it explicitly with a `<title>` and HTML `<meta>` tags in your design.

```html
<teleport to="head">
  <title>{{ report.title }}</title>
  <meta name="author" content="ACME Pentesting Ltd." />
  <meta name="description" content="Penetration test report" />
  <meta name="keywords" content="pentest, security, report" />
  <meta name="generator" content="SysReptor" />
  <meta name="dcterms.created" :content="formatDate(report.created, 'iso')" />
</teleport>
```

The following tags are supported. They are written to the PDF document info and to the XMP metadata.

| HTML tag | PDF document info | PDF XMP metadata |
|---|---|---|
| `<title>` | `Title` | `dc:title` |
| `<meta name="author">` | `Author` | `dc:creator` |
| `<meta name="description">` | `Subject` | `dc:description` |
| `<meta name="keywords">` | `Keywords` | `pdf:Keywords` |
| `<meta name="generator">` | `Creator` | `xmp:CreatorTool` |
| `<meta name="dcterms.created">` | `CreationDate` | `xmp:CreateDate` |
| `<meta name="dcterms.modified">` | `ModDate` | `xmp:ModifyDate` |
| `<meta name="Iptc4xmpExt:...">` | – | Matching [IPTC Extension](https://www.iptc.org/std/photometadata/specification/IPTC-PhotoMetadata) property |

The PDF filename can also be configured via meta tags. See [Filename](/designer/filenames).


## Example: AI marking

Use IPTC Extension properties to disclose that (parts of) the report were created with generative AI (for example for transparency obligations under the EU AI Act).
`DigitalSourceType` takes a value from the [IPTC Digital Source Type vocabulary](https://cv.iptc.org/newscodes/digitalsourcetype/), e.g. `trainedAlgorithmicMedia` for fully AI-generated content or `compositeWithTrainedAlgorithmicMedia` for content mixing human-written and AI-generated parts.

```html
<teleport to="head">
  <meta name="keywords" content="ai-generated" />
  <meta name="Iptc4xmpExt:DigitalSourceType" content="https://cv.iptc.org/newscodes/digitalsourcetype/compositeWithTrainedAlgorithmicMedia" />
  <meta name="Iptc4xmpExt:AISystemUsed" content="SysReptor AI" />
  <meta name="Iptc4xmpExt:AISystemVersionUsed" content="1.0" />
</teleport>
```
