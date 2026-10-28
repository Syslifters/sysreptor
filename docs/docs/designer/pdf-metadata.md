# PDF Metadata

Set PDF XMP metadata with HTML `<meta>` tags in your design. Inject them into the document head with Vue's `<teleport>`.

```html
<teleport to="head">
  <meta name="generator" content="SysReptor" />
  <meta name="keywords" content="pentest, security, report" />
  <meta name="dcterms.created" :content="report.report_date" />
</teleport>
```

| HTML | XMP |
|---|---|
| `<title>` | `dc:title` (defaults to `report.title`) |
| `author` | `dc:creator` |
| `description` | `dc:description` |
| `keywords` | `pdf:Keywords` |
| `generator` | `xmp:CreatorTool` |
| `dcterms.created` / `dcterms.modified` | `xmp:CreateDate` / `xmp:ModifyDate` |
| `Iptc4xmpExt:...` | Matching IPTC Extension property |

## Example: AI marking

Use IPTC Extension fields to disclose generative AI involvement (for example for transparency under the EU AI Act). Property names after `Iptc4xmpExt:` are case-sensitive.

```html
<teleport to="head">
  <meta name="keywords" content="AI-assisted, pentest report" />
  <meta name="Iptc4xmpExt:DigitalSourceType" content="https://cv.iptc.org/newscodes/digitalsourcetype/compositeWithTrainedAlgorithmicMedia" />
  <meta name="Iptc4xmpExt:AISystemUsed" content="SysReptor AI" />
  <meta name="Iptc4xmpExt:AISystemVersionUsed" content="1.0" />
</teleport>
```
