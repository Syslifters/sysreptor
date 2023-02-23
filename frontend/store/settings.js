import { set } from "vue";

export const state = () => ({
  autoSaveEnabled: true,
  markdownEditorMode: 'markdown', // 'markdown', 'preview', 'markdown-preview'
  spellcheckEnabled: true,
  reportInputMenuSize: 15,
  templateInputMenuSize: 15,
  notebookInputMenuSize: 15, 
  reportFieldDefinitionMenuSize: 15,
  findingFieldDefinitionMenuSize: 15,
  templateFieldFilterDesign: 'all',
  templateFieldFilterHiddenFields: [],
  noteExpandStates: {},
});

export const mutations = {
  updateAutoSaveEnabled(state, val) {
    state.autoSaveEnabled = val;
  },
  updateReportFieldDefinitionMenuSize(state, val) {
    state.reportFieldDefinitionMenuSize = val;
  },
  updateFindingFieldDefinitionMenuSize(state, val) {
    state.findingFieldDefinitionMenuSize = val;
  },
  updateReportInputMenuSize(state, val) {
    state.reportInputMenuSize = val;
  },
  updateTemplateInputMenuSize(state, val) {
    state.templateInputMenuSize = val;
  },
  updateNotebookInputMenuSize(state, val) {
    state.notebookInputMenuSize = val;
  },
  updateMarkdownEditorMode(state, val) {
    state.markdownEditorMode = val;
  },
  updateSpellcheckEnabled(state, val) {
    state.spellcheckEnabled = val;
  },
  updateTemplateFieldFilterDesign(state, val) {
    state.templateFieldFilterDesign = val;
  },
  updateTemplateFieldFilterHiddenFields(state, val) {
    state.templateFieldFilterHiddenFields = val;
  },
  setNoteExpandState(state, { noteId, isExpanded }) {
    set(state.noteExpandStates, noteId, isExpanded);
  },
}

export const getters = {
  isNoteExpanded: state => (noteId) => {
    const val = state.noteExpandStates[noteId];
    return val === undefined ? true : val;
  },
};
