import { describe, test, expect } from 'vitest';
import { formatHtmlToMarkdown } from '@sysreptor/markdown';

describe('HTML to Markdown Conversion', () => {

  for (const [html, markdown] of Object.entries({
    // Basic text
    'This is plain text': 'This is plain text',
    '<p>First paragraph</p><p>Second paragraph</p>': 'First paragraph\n\nSecond paragraph',
    'Line one<br>Line two<br/>Line three': 'Line one\\\nLine two\\\nLine three',
    '<p>This is <strong>bold</strong> text</p>': 'This is **bold** text',
    '<p>This is <b>bold</b> text</p>': 'This is **bold** text',
    '<p>This is <i>italic</i> text</p>': 'This is *italic* text',
    '<p>This is <em>italic</em> text</p>': 'This is *italic* text',
    '<p>This is <del>deleted</del> text</p>': 'This is ~~deleted~~ text',
    '<p>This is <code>inline code</code> text</p>': 'This is `inline code` text',
    // '<p>This is <u>underlined</u> text</p>': 'This is <u>underlined</u> text',
    '<p>Text with <strong>bold <em>and italic</em></strong> formatting</p>': 'Text with **bold *and italic*** formatting',
    // Headings
    '<h1>Heading 1</h1>': '# Heading 1',
    '<h2>Heading 2</h2>': '## Heading 2',
    '<h3>Heading 3</h3>': '### Heading 3',
    '<h4>Heading 4</h4>': '#### Heading 4',
    '<h5>Heading 5</h5>': '##### Heading 5',
    '<h6>Heading 6</h6>': '###### Heading 6',
    '<h2>Heading with <strong>bold</strong> text</h2>': '## Heading with **bold** text',
    // Lists
    '<ul><li>First item</li><li>Second item</li><li>Third item</li></ul>': '* First item\n* Second item\n* Third item',
    '<ol><li>First item</li><li>Second item</li><li>Third item</li></ol>': '1. First item\n2. Second item\n3. Third item',
    '<ul><li>First item<ul><li>Nested item 1</li><li>Nested item 2</li></ul></li><li>Second item</li></ul>': '* First item\n\n  * Nested item 1\n  * Nested item 2\n\n* Second item',
    '<ul><li><strong>Bold</strong> item</li><li><em>Italic</em> item</li></ul>': '* **Bold** item\n* *Italic* item',
    '<ul class="contains-task-list"><li class="task-list-item"><input type="checkbox" checked> Completed task</li><li class="task-list-item"><input type="checkbox"> Incomplete task</li></ul>': '* [x] Completed task\n* [ ] Incomplete task',
    // Links
    '<a href="https://example.com">Example Link</a>': '[Example Link](https://example.com)',
    '<a>Just text</a>': 'Just text',
    '<a href="">Empty link</a>': 'Empty link',
    '<p>Visit <a href="https://example.com">our website</a> for more info</p>': 'Visit [our website](https://example.com) for more info',
    // Code blocks
    '<pre>console.log("Hello World");</pre>': '```\nconsole.log("Hello World");\n```',
    '<pre><code>function test() {\n  return true;\n}</code></pre>': '```\nfunction test() {\n  return true;\n}\n```',
    '<pre><code class="language-javascript">const x = 5;</code></pre>': '```javascript\nconst x = 5;\n```',
    // Blockquotes
    '<blockquote>This is a quote</blockquote>': '> This is a quote',
    '<blockquote><p>This is a quoted paragraph</p></blockquote>': '> This is a quoted paragraph',
    // Tables
    '<table>\n<thead>\n<tr><th>Header 1</th><th>Header 2</th></tr>\n</thead>\n<tbody>\n<tr><td>Cell 1</td><td>Cell 2</td></tr>\n<tr><td>Cell 3</td><td>Cell 4</td></tr>\n</tbody>\n</table>': '| Header 1 | Header 2 |\n| -------- | -------- |\n| Cell 1   | Cell 2   |\n| Cell 3   | Cell 4   |',
    '<table>\n<tr><td>Cell 1</td><td>Cell 2</td></tr>\n<tr><td>Cell 3</td><td>Cell 4</td></tr>\n</table>': '|        |        |\n| ------ | ------ |\n| Cell 1 | Cell 2 |\n| Cell 3 | Cell 4 |',
    // Edge cases
    '': '',
    '   \n\t  ': '',
    '<p></p><div></div><span></span>': '',
    '<p>Text with    multiple spaces</p>': 'Text with multiple spaces',
    '<p>&lt;script&gt; &amp; &quot;quotes&quot; &apos;apostrophe&apos;</p>': '\\<script> & "quotes" \'apostrophe\'',
    '<p>Text</p><!-- This is a comment --><p>More text</p>': 'Text\n\nMore text',
    '<custom-element>Custom content</custom-element>': 'Custom content',
    '<p>Text with * asterisk and _ underscore and # hash</p>': 'Text with \\* asterisk and \\_ underscore and # hash',
    '<p>Path: C:\\Users\\Name</p>': 'Path: C:\\Users\\Name',
  })) {
    test(html, () => {
      const result = formatHtmlToMarkdown(html);
      expect(result.trim()).toBe(markdown);
    });
  }

  test('Excel table', () => {
    const html = `
      <div ccp_infra_version='3' ccp_infra_timestamp='1751452925980' ccp_infra_user_hash='2269577756' ccp_infra_copy_id='1db8ef04-e9dc-4f0f-a09e-eb6a292d9536' data-ccp-timestamp='1751452925980'>
      <html>
        <head>
          <meta http-equiv=Content-Type content="text/html; charset=utf-8">
          <meta name=ProgId content=Excel.Sheet>
          <meta name=Generator content="Microsoft Excel 15">
          <style>
          table
            {mso-displayed-decimal-separator:"\\,";
            mso-displayed-thousand-separator:"\\.";}
          tr
            {mso-height-source:auto;}
          col
            {mso-width-source:auto;}
          td
            {padding-top:1px;
            padding-right:1px;
            padding-left:1px;
            mso-ignore:padding;
            color:windowtext;
            font-size:11.0pt;
            font-weight:400;
            font-style:normal;
            text-decoration:none;
            font-family:"Trebuchet MS", sans-serif;
            mso-font-charset:0;
            text-align:right;
            vertical-align:bottom;
            border:none;
            white-space:nowrap;
            mso-rotate:0;}
          .xl102
            {font-weight:700;}
          .xl103
            {font-style:italic;}
          .xl104
            {color:black;
            font-family:"Trebuchet MS";
            mso-generic-font-family:auto;
            mso-font-charset:0;}
          </style>
        </head>
        <body link="#0563C1" vlink="#954F72">
          <table width=144 style='border-collapse:collapse;width:108pt'>
            <!--StartFragment-->
            <col width=72 style='width:54pt' span=2>
            <tr height=22 style='height:16.5pt'>
              <td width=72 height=22 class=xl105 style='width:54pt;height:16.5pt'>Cell1</td>
              <td width=72 class=xl105 style='width:54pt'>Cell2</td>
            </tr>
            <tr height=22 style='height:16.5pt'>
              <td height=22 style='height:16.5pt'>Cell3</td>
              <td>Cell4</td>
            </tr>
            <!--EndFragment-->
          </table>
        </body>
      </html>
    </div>`;
    const expected = `|       |       |\n| ----- | ----- |\n| Cell1 | Cell2 |\n| Cell3 | Cell4 |`;
    const result = formatHtmlToMarkdown(html).trim();
    expect(result).toBe(expected);
  });

  test('LibreOffice table', () => {
    const html = `
    <!DOCTYPE html>

    <html>
    <head>
      
      <meta http-equiv="content-type" content="text/html; charset=utf-8"/>
      <title></title>
      <meta name="generator" content="LibreOffice 25.2.4.3 (Linux)"/>
      <style type="text/css">
        body,div,table,thead,tbody,tfoot,tr,th,td,p { font-family:"Liberation Sans"; font-size:x-small }
        a.comment-indicator:hover + comment { background:#ffd; position:absolute; display:block; border:1px solid black; padding:0.5em;  } 
        a.comment-indicator { background:red; display:inline-block; border:1px solid black; width:0.5em; height:0.5em;  } 
        comment { display:none;  } 
      </style>
      
    </head>

    <body>
      <table cellspacing="0" border="0">
        <colgroup span="2" width="171"></colgroup>
        <tr>
          <td height="34" align="left" data-sheets-value="{ &quot;1&quot;: 2, &quot;2&quot;: &quot;Cell1&quot;}">Cell1</td>
          <td align="left" data-sheets-value="{ &quot;1&quot;: 2, &quot;2&quot;: &quot;Cell2&quot;}">Cell2</td>
        </tr>
        <tr>
          <td height="34" align="left" data-sheets-value="{ &quot;1&quot;: 2, &quot;2&quot;: &quot;Cell3&quot;}">Cell3</td>
          <td align="left" data-sheets-value="{ &quot;1&quot;: 2, &quot;2&quot;: &quot;Cell4&quot;}">Cell4</td>
        </tr>
      </table>
    </body>

    </html>`;
    const expected = `|       |       |\n| :---- | :---- |\n| Cell1 | Cell2 |\n| Cell3 | Cell4 |`;
    const result = formatHtmlToMarkdown(html).trim();
    expect(result).toBe(expected);
  });
});
