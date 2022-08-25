export const state = () => ({
  autoSaveEnabled: true,
  markdownEditorMode: 'markdown', // 'markdown', 'preview', 'markdown-preview'
  reportInputMenuSize: 15,
  templateInputMenuSize: 15,
  reportFieldDefinitionMenuSize: 15,
  findingFieldDefinitionMenuSize: 15,
  templateFieldVisibilityFilter: 'all',
});

export const mutations = {
  updateAutoSaveEnabled(state, val) {
    state.autoSaveEnabled = val;
  },
  updateMarkdownEditorPreviewModel(state, val) {
    state.markdownEditorPreviewMode = val;
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
  updateMarkdownEditorMode(state, val) {
    state.markdownEditorMode = val;
  },
  updateTemplateFieldVisibilityFilter(state, val) {
    state.templateFieldVisibilityFilter = val;
  }
}
