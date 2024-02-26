export { EditorState, EditorSelection, ChangeSet } from '@codemirror/state';
export { EditorView, ViewUpdate, tooltips, scrollPastEnd, keymap, lineNumbers, drawSelection, rectangularSelection, crosshairCursor, } from '@codemirror/view';
export { history, historyKeymap, defaultKeymap, indentWithTab, undo, redo, undoDepth, redoDepth } from '@codemirror/commands';
export { forceLinting, setDiagnostics } from '@codemirror/lint';
export { closeBrackets } from "@codemirror/autocomplete";
export { MergeView } from '@codemirror/merge';
export { syntaxHighlighting, indentUnit } from '@codemirror/language';
export { vueLanguage } from '@codemirror/lang-vue';
export { cssLanguage } from '@codemirror/lang-css';
export { markdown } from './language';
export { createEditorExtensionToggler } from './utils';
export { spellcheck, spellcheckTheme } from './spellcheck';
export { highlightTodos } from './todos';
export { markdownHighlightStyle, markdownHighlightCodeBlocks } from './highlight';
export { collab, receiveUpdates, sendableUpdates } from './collab';
export { 
  toggleStrong, toggleEmphasis, toggleStrikethrough, toggleFootnote,
  toggleListUnordered, toggleListOrdered, toggleTaskList,
  toggleLink, insertCodeBlock, insertTable, 
  isTypeInSelection, isTaskListInSelection,
  insertNewlineContinueMarkup
} from './commands';
import 'highlight.js/styles/default.css';
