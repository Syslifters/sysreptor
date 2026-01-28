import { describe, it, expect } from 'vitest';
import { Validator } from '@cfworker/json-schema';
import { markdownToADF } from '../frontend/utils/md2adf';
import adfSchema from './adf.schema.json';

const adfValidator = new Validator(adfSchema);


describe('Test markdown to ADF', () => {
  const testCases: Record<string, any> = {
    // Paragraphs
    '': [],
    '   \n\n   ': [],
    'Hello world': { type: 'paragraph', content: [{ type: 'text', text: 'Hello world' }]},
    'First paragraph\n\nSecond paragraph': [
      { type: 'paragraph', content: [{ type: 'text', text: 'First paragraph' }] },
      { type: 'paragraph', content: [{ type: 'text', text: 'Second paragraph' }] },
    ],
    'Line1  \nLine2': { type: 'paragraph', content: [
      { type: 'text', text: 'Line1' },
      { type: 'hardBreak' },
      { type: 'text', text: 'Line2' },
    ]},
    'Line1\\\nLine2': { type: 'paragraph', content: [
      { type: 'text', text: 'Line1' },
      { type: 'hardBreak' },
      { type: 'text', text: 'Line2' },
    ]},
    // Headings
    '# Heading 1': { type: 'heading', attrs: { level: 1 }, content: [{ type: 'text', text: 'Heading 1' }] },
    '## Heading 2': { type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: 'Heading 2' }] },
    'Heading\n=======': { type: 'heading', attrs: { level: 1 }, content: [{ type: 'text', text: 'Heading' }] },
    'Heading\n-------': { type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: 'Heading' }] },
    '## **Bold** and *italic*': { type: 'heading', attrs: { level: 2 }, content: [
      { type: 'text', text: 'Bold', marks: [{ type: 'strong' }] },
      { type: 'text', text: ' and ' },
      { type: 'text', text: 'italic', marks: [{ type: 'em' }] },
    ]},
    // Text formatting
    '**bold text**': { type: 'text', text: 'bold text', marks: [{ type: 'strong' }] },
    '__bold text__': { type: 'text', text: 'bold text', marks: [{ type: 'strong' }] },
    '*italic text*': { type: 'text', text: 'italic text', marks: [{ type: 'em' }] },
    '_italic text_': { type: 'text', text: 'italic text', marks: [{ type: 'em' }] },
    '~~strikethrough~~': { type: 'text', text: 'strikethrough', marks: [{ type: 'strike' }] },
    '**bold *and italic ~~and strike `and code` after~~***': [
      { type: 'text', text: 'bold ', marks: [{ type: 'strong' }] },
      { type: 'text', text: 'and italic ', marks: [{ type: 'em' }, { type: 'strong' }] },
      { type: 'text', text: 'and strike ', marks: [{ type: 'strike' }, { type: 'em' }, { type: 'strong' }] },
      { type: 'text', text: 'and code', marks: [{ type: 'code' }] },
      { type: 'text', text: ' after', marks: [{ type: 'strike' }, { type: 'em' }, { type: 'strong' }] },
    ],
    // Code
    '`code`': { type: 'text', text: 'code', marks: [{ type: 'code' }] },
    '```code `with` backticks ```': { type: 'text', text: 'code `with` backticks ', marks: [{ type: 'code' }] },
    '```\ncode\n\nhere\n```': { type: 'codeBlock', attrs: {}, content: [{ type: 'text', text: 'code\n\nhere' }] },
    '```python\nprint("hello")\n```': { type: 'codeBlock', attrs: { language: 'python' }, content: [{ type: 'text', text: 'print("hello")' }] },
    // Math
    '$math$': { type: 'text', text: 'math', marks: [{ type: 'code' }] },
    '$$\nmath\n$$': { type: 'codeBlock', attrs: { language: 'math' }, content: [{ type: 'text', text: 'math' }] },
    // Links
    '[Link text](https://example.com)': { type: 'text', text: 'Link text', marks: [{ type: 'link', attrs: { href: 'https://example.com' } }] },
    // Images
    '![Alt text](image.png)': { type: 'text', text: '![Alt text](image.png)' },
    '![Alt text](https://example.com/image.jpg)': { type: 'text', text: '![Alt text](https://example.com/image.jpg)' },
    '![](image.png)': { type: 'text', text: '![](image.png)' },
    '![Alt](image.png "Title")': { type: 'text', text: '![Alt](image.png "Title")' },
    'Text with ![inline](/images/name/img.png) image': { type: 'text', text: 'Text with ![inline](/images/name/img.png) image' },
    // Lists
    '* Item 1\n* **Item 2**\n* `Item 3`': {
      type: 'bulletList',
      content: [
        { type: 'listItem', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Item 1' }] }] },
        { type: 'listItem', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Item 2', marks: [{ type: 'strong' }] }] }] },
        { type: 'listItem', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Item 3', marks: [{ type: 'code' }] }] }] },
      ],
    },
    '1. Item 1\n2. **Item 2**\n3. `Item 3`': {
      type: 'orderedList',
      content: [
        { type: 'listItem', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Item 1' }] }] },
        { type: 'listItem', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Item 2', marks: [{ type: 'strong' }] }] }] },
        { type: 'listItem', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Item 3', marks: [{ type: 'code' }] }] }] },
      ],
    },
    '* Item 1\n    1. Item 1.1\n    2. Item 1.2\n        * Item 1.2.1\n* Item 2': {
      type: 'bulletList',
      content: [
        { type: 'listItem', content: [
          { type: 'paragraph', content: [{ type: 'text', text: 'Item 1' }] },
          { type: 'orderedList', content: [
            { type: 'listItem', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Item 1.1' }] }] },
            { type: 'listItem', content: [
              { type: 'paragraph', content: [{ type: 'text', text: 'Item 1.2' }] },
              { type: 'bulletList', content: [
                { type: 'listItem', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Item 1.2.1' }] }] },
              ]},
            ]},
          ]},
        ]},
        { type: 'listItem', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Item 2' }] } ]}
    ]},
    // Blockquotes
    '> blockquote': { type: 'paragraph', content: [{ type: 'text', text: 'blockquote' }] },
    '> **text**\n> line2\n>\n>> blockquote': [
      { type: 'paragraph', content: [
        { type: 'text', text: 'text', marks: [{ type: 'strong' }] },
        { type: 'text', text: '\nline2' },
      ]},
      { type: 'paragraph', content: [{ type: 'text', text: 'blockquote' }] },
    ],
    // Tables
    '| Header1 | **Header2** |\n|----------|----------|\n| Cell 1   | `Cell2`   |': { type: 'table', content: [
      { type: 'tableRow', content: [
        { type: 'tableCell', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Header1' }]}] },
        { type: 'tableCell', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Header2', marks: [{ type: 'strong' }] }]}] },
      ]},
      { type: 'tableRow', content: [
        { type: 'tableCell', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Cell 1' }]}] },
        { type: 'tableCell', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Cell2', marks: [{ type: 'code' }] }]}] },
      ]},
    ]},
    // Unsupported features
    '<div>HTML content</div>': { type: 'text', text: '<div>HTML content</div>' },
    'text^[footnote] text': { type: 'text', text: 'text^[footnote] text' },
    '## Heading {#custom-id}': { type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: 'Heading ' }] },
    '{{ variable }}': { type: 'text', text: '{{ variable }}' },
    'TODO: markers': { type: 'text', text: 'TODO: markers' },
    '---': { type: 'text', text: '---' },
  };
  for (const [md, expected] of Object.entries(testCases)) {
    it(JSON.stringify(md).slice(1, -1), () => {
      let content = Array.isArray(expected) ? expected : [expected];
      if (content[0]?.type === 'text') {
        content = [{ type: 'paragraph', content }];
      }

      const adf = markdownToADF(md)
      expect(adf).toEqual({
        type: 'doc',
        version: 1,
        content,
      });
      expect(adfValidator.validate(adf).valid).toBe(true);
    });
  }
});


// describe('md2adf - Basic Markdown', () => {
//   describe('Images', () => {
//     const testCases = [
//       '![Alt text](image.png)',
//       '![Alt](image.png "Title")',
//       '![](image.png)',
//     ];

//     testCases.forEach((markdown) => {
//       it(`should convert: ${markdown}`, () => {
//         const result = markdownToADF(markdown);
//         expect(result.content[0].type).toBe('paragraph');
//       });
//     });
//   });
// });

