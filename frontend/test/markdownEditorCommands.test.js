import { EditorState, EditorSelection } from '@codemirror/state';
import { EditorView } from '@codemirror/view';
import { markdown } from 'reportcreator-markdown/editor/language.js';
import { syntaxHighlighting } from '@codemirror/language';
import { markdownHighlightStyle, markdownHighlightCodeBlocks } from 'reportcreator-markdown/editor/highlight.js';
import { toggleStrong, toggleEmphasis, toggleStrikethrough, toggleListUnordered, toggleListOrdered, toggleLink, insertCodeBlock, insertTable } from 'reportcreator-markdown/editor/commands.js';

function createEditorState(textWithSelection, cursorMarker = '|') {
  const parts = textWithSelection.split(cursorMarker);
  let selectionRange = null;
  if (parts.length === 2) {
    selectionRange = EditorSelection.cursor(parts[0].length)
  } else if (parts.length === 3) {
    selectionRange = EditorSelection.range(parts[0].length, parts[0].length + parts[1].length);
  } else {
    throw new Error('Invalid number of cursors in text');
  }

  return EditorState.create({
    doc: parts.join(''),
    selection: EditorSelection.create([selectionRange]),
    extensions: [
      markdown(),
      syntaxHighlighting(markdownHighlightStyle),
      markdownHighlightCodeBlocks,
    ]
  });
}

function testCommand(command, before, after, cursorMarker = '|') {
  test(before, () => {
    const view = new EditorView({ state: createEditorState(before, cursorMarker) })
    command({ state: view.state, dispatch: view.dispatch });
    const stateAfterActual = view.state;

    const stateAfterExpected = createEditorState(after, cursorMarker);
    expect(stateAfterActual.doc.toString()).toBe(stateAfterExpected.doc.toString());
    expect(stateAfterActual.selection.eq(stateAfterExpected.selection)).toBeTruthy();

    view.destroy();
  });
}

for (const toggleSequenceOptions of [
  { name: 'toggleStrong', command: toggleStrong, sequence: '**' },
  { name: 'toggleEmphasis', command: toggleEmphasis, sequence: '_' },
  { name: 'toggleStrikethrough', command: toggleStrikethrough, sequence: '~~' },
]) { 
  describe(toggleSequenceOptions.name, () => {
    const s = toggleSequenceOptions.sequence;
    for (const [before, after] of Object.entries({
      'a |text| b': `a ${s}|text|${s} b`,
      'a | b': `a ${s}|text|${s} b`,
      [`a ${s}te|xt${s} b`]: 'a te|xt b',
      [`a ${s}|text|${s} b`]: 'a |text| b',
      [`|a ${s}text${s} b|`]: "|a text b|",
      [`|a ${s}te|xt${s} b`]: "|a te|xt b",
      [`|a |${s}text${s} b`]: "|a |text b",
      // [`a ${s}|${s} b`]: "a | b",
      ...(s.length > 1 ? {
        [`|a ${s.slice(0, 1)}|${s.slice(1)}text${s} b`]: "|a |text b",
        [`a ${s.slice(0, 1)}|${s.slice(1)}text${s.slice(0, 1)}|${s.slice(1)} b`]: "a |text| b",
      } : {}),  
    })) { 
      testCommand(toggleSequenceOptions.command, before, after);
    }
  })
}

describe('toggleListUnordered', () => {
  for (const [before, after] of Object.entries({
    "|a\nb|": "|* a\n* b|",
    "a|aa\nb": "* a|aa\nb",
    "|* a\n* b|": "|a\nb|",
    "* a|\n* b": "a|\n* b",
    "|1. a\n2. b|": "|* a\n* b|",
    "1. |a\n2. b": "* |a\n2. b",
  })) {
    testCommand(toggleListUnordered, before, after);
  }
});

describe('toggleListOrdered', () => {
  for (const [before, after] of Object.entries({
    "|a\nb|": "|1. a\n2. b|",
    "a|aa\nb": "1. a|aa\nb",
    "|1. a\n2. b|": "|a\nb|",
    "1. a|\n2. b": "a|\n2. b",
    "|* a\n* b|": "|1. a\n2. b|",
    "* |a\n* b": "1. |a\n* b",
  })) {
    testCommand(toggleListOrdered, before, after);
  }
});

describe('toggleLink', () => {
  for (const [before, after] of Object.entries({
    "a | b": "a [|](https://) b",
    "a |text| b": "a [|text|](https://) b",
    "a [|text|]() b": "a |text| b",
    "a [te|xt]() b": "a te|xt b",
    "|a [text]() b|": "|a [text]() b|",
    "|a [te|xt]() b": "|a [te|xt]() b",
  })) {
    testCommand(toggleLink, before, after);
  }
});

describe('insertCodeBlock', () => {
  for (const [before, after] of Object.entries({
    "a\n|\nb": "a\n\n```\n|\n```\nb",
    "a\n|code\ncode|\nb": "a\n\n```\n|code\ncode|\n```\nb",
    "a\nc|od|e\nb": "a\n\n```\nc|od|e\n```\nb",
  })) {
    testCommand(insertCodeBlock, before, after);
  }
});

describe('insertTable', () => {
  testCommand(insertTable, 'a\n§\nb', 'a\n§\n| Column1 | Column2 | Column3 |\n| ------- | ------- | ------- |\n| Text    | Text    | Text    |\n\n\nb', '§');
});
