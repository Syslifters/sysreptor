export { EditorState, EditorSelection, SelectionRange, ChangeSet, Text, Transaction, type Extension } from '@codemirror/state';
export { EditorView, ViewUpdate, tooltips, scrollPastEnd, keymap, lineNumbers, drawSelection, rectangularSelection, crosshairCursor, dropCursor } from '@codemirror/view';
export { history, historyKeymap, defaultKeymap, indentWithTab, undo, redo, undoDepth, redoDepth } from '@codemirror/commands';
export { forceLinting, setDiagnostics } from '@codemirror/lint';
export { closeBrackets, CompletionContext, autocompletion } from "@codemirror/autocomplete";
export { search, searchKeymap, SearchQuery, SearchCursor } from '@codemirror/search'
export { MergeView } from '@codemirror/merge';
export { syntaxHighlighting, syntaxTree, indentUnit } from '@codemirror/language';
export type { SyntaxNode, Tree } from '@lezer/common';
export { vueLanguage } from '@codemirror/lang-vue';
export { cssLanguage } from '@codemirror/lang-css';
export { markdown, compareTree } from './language';
export { createEditorExtensionToggler } from './utils';
export { spellcheck, spellcheckTheme } from './spellcheck';
export { highlightTodos } from './todos';
export { 
  toggleStrong, toggleEmphasis, toggleStrikethrough, toggleFootnote, toggleCodeText,
  toggleListUnordered, toggleListOrdered, toggleTaskList, toggleBlockQuote,
  toggleLink, insertCodeBlock, insertTable, insertText,
  isTypeInSelection, isTaskListInSelection,
  insertNewlineContinueMarkup
} from './commands';
export { setRemoteClients, remoteSelection } from './awareness';
export { setComments, commentsExtension } from './comments';
export { setSearchGlobalQuery, searchGlobalExtensions, CustomizedSearchPanel } from './search';
import 'highlight.js/styles/default.css';
