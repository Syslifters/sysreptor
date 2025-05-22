import { compareTree, EditorState, markdown, syntaxTree } from "@sysreptor/markdown/editor";
import { describe, expect, test } from "vitest";


function paragraph(length: number = 198) {
  const words = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. ';
  return words.repeat(Math.ceil(length / words.length)).slice(0, length);
}

function doc(blocks: string[]) {
  return blocks.join('\n\n');
}


function testIncrementalParsing(doc: string, changes: {insert?: string, delete?: number}, options?: { fullReparse?: boolean } ) {
  const cursorPos = doc.indexOf('|');
  doc = doc.replaceAll('|', '');

  const stateOriginal = EditorState.create({
    doc: doc,
    extensions: [markdown()],
  })
  const syntaxTreeOriginal = syntaxTree(stateOriginal);

  const stateIncremental = stateOriginal.update({ 
    changes: { from: cursorPos, to: cursorPos + (changes.delete || 0), insert: changes.insert || '' }, 
  }).state;
  const syntaxTreeIncremental = syntaxTree(stateIncremental);

  const stateFull = EditorState.create({
    doc: stateIncremental.doc.toString(),
    extensions: [markdown()],
  })
  const syntaxTreeFull = syntaxTree(stateFull);

  // Check if syntax trees are the same
  expect(compareTree(syntaxTreeIncremental, syntaxTreeFull)).toBe(true);

  // Check if parts of the previous syntax tree were reused or if it was a full reparse of the whole document
  const blocksReused = syntaxTreeIncremental.children.some(b => syntaxTreeOriginal.children.includes(b));
  expect(!blocksReused).toBe(options?.fullReparse ?? false);
}

const defaultDoc = doc([
  '# headline', 
  paragraph(), 
  `\`\`\`python\nline1\nline2\nline3\n\`\`\``, 
  paragraph(), 
  '![image](/images/name/test.png)',
  paragraph(),
])

describe('Incremental Markdown Parsing', () => {
  const testCases = [
    {
      name: 'Empty doc begin writing',
      doc: '|',
      changes: { insert: 'a'},
      fullReparse: true,
    },
    {
      name: 'Empty doc insert',
      doc: '|',
      changes: { insert: 'text **strong** text _emphasis_ text ~~strikethrough~~ text [link](https://example.com) text `code` text'},
      fullReparse: true,
    },
    {
      name: 'Insert at start',
      doc: '|' + defaultDoc,
      changes: { insert: 'a'},
    },
    {
      name: 'Delete at start',
      doc: '|' + defaultDoc,
      changes: { delete: 1 },
    },
    {
      name: 'Insert at end',
      doc: defaultDoc + '|',
      changes: { insert: 'a'},
    },
    {
      name: 'Delete at end',
      doc: defaultDoc + '|a',
      changes: { delete: 1},
    },
    {
      name: 'Insert at end after multiple empty newlines',
      doc: defaultDoc + '\n\n\n\n|',
      changes: { insert: 'a'},
    },
    {
      name: 'Delete at end after multiple empty newlines',
      doc: defaultDoc + '\n\n\n|\n',
      changes: { delete: 1},
    },
    {
      name: 'Insert inside paragraph',
      doc: defaultDoc.slice(0, 343) + '|' + defaultDoc.slice(343),
      changes: { insert: 'a'},
    },
    {
      name: 'Delete inside paragraph',
      doc: defaultDoc.slice(0, 343) + '|' + defaultDoc.slice(343),
      changes: { delete: 1},
    },
    {
      name: 'Insert multiple characters inside paragraph',
      doc: defaultDoc.slice(0, 343) + '|' + defaultDoc.slice(343),
      changes: { insert: 'multiple characters' },
    },
    {
      name: 'Delete multiple characters inside paragraph',
      doc: defaultDoc.slice(0, 343) + '|' + defaultDoc.slice(343),
      changes: { delete: 15 },
    },
    {
      name: 'Replace multiple characters inside paragraph',
      doc: defaultDoc.slice(0, 343) + '|' + defaultDoc.slice(343),
      changes: { delete: 20, insert: 'new' },
    },
    {
      name: 'Insert at start of paragraph',
      doc: doc([paragraph(), '|' + paragraph(), paragraph()]),
      changes: { insert: 'a' },
    },
    {
      name: 'Delete at start of paragraph',
      doc: doc([paragraph(), '|' + paragraph(), paragraph()]),
      changes: { delete: 1 },
    },
    {
      name: 'Insert at end of paragraph',
      doc: doc([paragraph(), paragraph() + '|', paragraph()]),
      changes: { insert: 'a' },
    },
    {
      name: 'Delete at end of paragraph',
      doc: doc([paragraph(), paragraph() + '|a', paragraph()]),
      changes: { delete: 1 },
    },
    {
      name: 'Insert newline after paragraph',
      doc: doc([paragraph() + '|', '', paragraph()]),
      changes: { insert: '\n' },
    },
    {
      name: 'Insert newline after paragraph',
      doc: doc([paragraph() + '\n|', '', paragraph()]),
      changes: { insert: '\n' },
    },
    {
      name: 'Start new paragraph',
      doc: doc([paragraph(), '|', paragraph()]),
      changes: { insert: 'new paragraph' },
    },
    {
      name: 'Delete paragraph',
      doc: doc([paragraph(), '|a', paragraph()]),
      changes: { delete: 1 },
    },
    {
      name: 'Delete newline after paragraph',
      doc: doc([paragraph() + '\n|\n', '', '', paragraph(), paragraph()]),
      changes: { delete: 1 },
    },
    {
      name: 'Merge 2 paragraphs',
      doc: doc([paragraph() + '|', paragraph(), paragraph(), paragraph(), paragraph()]),
      changes: { delete: 1 },
      fullReparse: true,
    },
    

    {
      name: 'Insert changes markdown construct (link to image)',
      doc: doc([paragraph(), '|[](/images/name/test.png)', paragraph()]),
      changes: { insert: '!' },
    },
    {
      name: 'Delete changes markdown construct (image to link)',
      doc: doc([paragraph(), '|![image](/images/name/test.png)', paragraph()]),
      changes: { delete: 1},
    },
    {
      name: 'Insert changes inline markdown construct (strong)',
      doc: doc([paragraph(), 'text **strong*| text', paragraph()]),
      changes: { insert: '*'},
    },
    {
      name: 'Delete changes inline markdown construct (strong)',
      doc: doc([paragraph(), 'text **strong*|* text', paragraph()]),
      changes: { delete: 1},
    },
    {
      name: 'Start code block: causes following blocks to be parsed differently',
      doc: doc([paragraph(), '``|', paragraph(), paragraph(), paragraph()]),
      changes: { insert: '`' },
      fullReparse: true,
    },
    {
      name: 'End code block: causes following blocks to be parsed differently',
      doc: doc([paragraph(), '```\ncode\n``|', paragraph(), paragraph(), paragraph()]),
      changes: { insert: '`' },
    },
    {
      name: 'Insert inside code block',
      doc: doc([paragraph(), '```', paragraph() + '|' + paragraph() ,'```', paragraph()]),
      changes: { insert: 'a' },
    },
    {
      name: 'Incremental parsing not possible: reference link',
      doc: doc([paragraph(), 'text| [link][ref]', paragraph(), '[ref]: https://example.com']),
      changes: { insert: 'a' },
      fullReparse: true,
    },
    {
      name: 'Incremental parsing not possible: definition',
      doc: doc([paragraph(), paragraph(), '[ref]: https://exa|mple.com',]),
      changes: { insert: 'a' },
      fullReparse: true,
    },
    {
      name: 'Incremental parsing possible: reference link in unchanged block',
      doc: doc([paragraph() + '|', paragraph(), paragraph(), 'text [link][ref]', '[ref]: https://example.com']),
      changes: { insert: 'a' },
    },
    // HTML test cases
    {
      name: 'HTML block: Insert incomplete HTML tag',
      doc: doc([paragraph(), '<div|', paragraph()]),
      changes: { insert: '>' },
    },
    {
      name: 'HTML block: Complete HTML block with closing tag',
      doc: doc([paragraph(), '<div>\nsome content\n</div|', paragraph()]),
      changes: { insert: '>' },
    },
    {
      name: 'HTML block: Insert content inside HTML block',
      doc: doc([paragraph(), '<div>\nsome content|\n</div>', paragraph()]),
      changes: { insert: ' with HTML' },
    },
    {
      name: 'Inline HTML: Insert tag inside paragraph',
      doc: doc([paragraph(), 'This is a paragraph with | elements', paragraph()]),
      changes: { insert: ' <span>inline HTML</span>' },
    },
    {
      name: 'HTML comments: Start new comment',
      doc: doc([paragraph(), '<!-|', paragraph(), paragraph(), paragraph()]),
      changes: { insert: '-' },
      fullReparse: true,
    },
    {
      name: 'HTML comments: Complete comment',
      doc: doc([paragraph(), '<!--', paragraph(), '--|', paragraph(), paragraph()]),
      changes: { insert: ' >' },
    },
    {
      name: 'HTML comments: Insert content inside comment',
      doc: doc([paragraph(), '<!--', paragraph(), '|', paragraph(), '-->', paragraph()]),
      changes: { insert: 'comment ' },
    },
  ];

  for (const testCase of testCases) {
    test(testCase.name, () => {
      testIncrementalParsing(testCase.doc, testCase.changes, { fullReparse: testCase.fullReparse });
    });
  }
});
