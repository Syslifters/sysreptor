import { EditorState, EditorSelection } from '@codemirror/state';
import { EditorView, ViewUpdate, tooltips, scrollPastEnd, keymap, lineNumbers } from '@codemirror/view';
import { history, historyKeymap, defaultKeymap, indentWithTab, undo, redo, undoDepth, redoDepth } from '@codemirror/commands';
import { forceLinting, setDiagnostics } from '@codemirror/lint';
import { MergeView } from '@codemirror/merge';
import { syntaxHighlighting, indentUnit } from '@codemirror/language';
import { vueLanguage } from '@codemirror/lang-vue';
import { cssLanguage } from '@codemirror/lang-css';
import { markdown } from 'reportcreator-markdown/editor/language';
import { createEditorExtensionToggler } from 'reportcreator-markdown/editor/utils';
import { spellcheck, spellcheckTheme } from 'reportcreator-markdown/editor/spellcheck';
import { highlightTodos } from 'reportcreator-markdown/editor/todos';
import { markdownHighlightStyle, markdownHighlightCodeBlocks } from 'reportcreator-markdown/editor/highlight';
import { toggleStrong, toggleEmphasis, toggleStrikethrough, toggleListUnordered, toggleListOrdered, toggleLink, insertCodeBlock, insertTable, isTypeInSelection, insertNewlineContinueMarkup } from 'reportcreator-markdown/editor/commands';
import 'highlight.js/styles/default.css';

export {
  EditorState, EditorView, ViewUpdate, EditorSelection, MergeView,
  tooltips, scrollPastEnd, forceLinting, setDiagnostics,
  history, historyKeymap, keymap, undo, redo, undoDepth, redoDepth,
  vueLanguage, cssLanguage,
  createEditorExtensionToggler, spellcheck, spellcheckTheme, highlightTodos,
  lineNumbers, indentUnit, defaultKeymap, indentWithTab, markdown,
  syntaxHighlighting, markdownHighlightStyle, markdownHighlightCodeBlocks,
  toggleStrong, toggleEmphasis, toggleStrikethrough,
  toggleListUnordered, toggleListOrdered,
  toggleLink, insertCodeBlock, insertTable, isTypeInSelection, insertNewlineContinueMarkup
}