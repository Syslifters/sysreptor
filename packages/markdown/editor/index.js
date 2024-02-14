export { EditorState, EditorSelection } from '@codemirror/state';
export { EditorView, ViewUpdate, tooltips, scrollPastEnd, keymap, lineNumbers, drawSelection, rectangularSelection, crosshairCursor, } from '@codemirror/view';
export { history, historyKeymap, defaultKeymap, indentWithTab, undo, redo, undoDepth, redoDepth } from '@codemirror/commands';
export { forceLinting, setDiagnostics } from '@codemirror/lint';
export { closeBrackets } from "@codemirror/autocomplete";
export { MergeView } from '@codemirror/merge';
export { syntaxHighlighting, indentUnit } from '@codemirror/language';
export { vueLanguage } from '@codemirror/lang-vue';
export { cssLanguage } from '@codemirror/lang-css';
export { markdown } from 'reportcreator-markdown/editor/language';
export { createEditorExtensionToggler } from 'reportcreator-markdown/editor/utils';
export { spellcheck, spellcheckTheme } from 'reportcreator-markdown/editor/spellcheck';
export { highlightTodos } from 'reportcreator-markdown/editor/todos';
export { markdownHighlightStyle, markdownHighlightCodeBlocks } from 'reportcreator-markdown/editor/highlight';
export { 
  toggleStrong, toggleEmphasis, toggleStrikethrough, toggleFootnote,
  toggleListUnordered, toggleListOrdered, toggleTaskList,
  toggleLink, insertCodeBlock, insertTable, 
  isTypeInSelection, isTaskListInSelection,
  insertNewlineContinueMarkup
} from 'reportcreator-markdown/editor/commands';
import 'highlight.js/styles/default.css';
