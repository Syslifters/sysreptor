import { CvssVersion } from "@base/utils/cvss/base";
import { MarkdownEditorMode, CommentStatus, type FilterValue } from "#imports";

export const useLocalSettings = defineStore('settings', {
  state: () => ({
    autoSaveEnabled: true,
    reportingMarkdownEditorMode: MarkdownEditorMode.MARKDOWN_AND_PREVIEW as MarkdownEditorMode,
    projectNoteMarkdownEditorMode: MarkdownEditorMode.MARKDOWN_AND_PREVIEW as MarkdownEditorMode,
    userNoteMarkdownEditorMode: MarkdownEditorMode.MARKDOWN_AND_PREVIEW as MarkdownEditorMode,
    designMarkdownEditorMode: MarkdownEditorMode.MARKDOWN_AND_PREVIEW as MarkdownEditorMode,
    templateMarkdownEditorMode: MarkdownEditorMode.MARKDOWN_AND_PREVIEW as MarkdownEditorMode,
    sharedNoteMarkdownEditorMode: MarkdownEditorMode.PREVIEW as MarkdownEditorMode,
    reportingSpellcheckEnabled: true,
    projectNoteSpellcheckEnabled: true,
    userNoteSpellcheckEnabled: true,
    designSpellcheckEnabled: true,
    templateSpellcheckEnabled: true,
    reportInputMenuSizePx: 300,
    templateInputMenuSizePx: 300,
    notebookInputMenuSizePx: 300,
    reportFieldDefinitionMenuSizePx: 300,
    findingFieldDefinitionMenuSizePx: 300,
    defaultNotesDefinitionMenuSizePx: 300,
    reportingCommentSidebarVisible: false,
    reportingSidebarSizePx: 300,
    reportingCommentStatusFilter: CommentStatus.OPEN as CommentStatus|'all',
    reportingChatSidebarVisible: false,
    reportingChatAgent: 'project_ask' as 'project_ask'|'project_agent',
    projectListOrdering: null as string|null,
    designListOrdering: null as string|null,
    templateListOrdering: null as string|null,
    projectListPinnedFilters: [] as FilterValue[],
    designListPinnedFilters: [] as FilterValue[],
    templateListPinnedFilters: [] as FilterValue[],
    userListOrdering: null as string|null,
    templateFieldFilterDesign: 'all',
    templateFieldFilterHiddenFields: [] as string[],
    noteExpandStates: {} as {[noteId: string]: boolean},
    cvssVersion: CvssVersion.CVSS31,
    subDrawerExpanded: true,
    pluginMenuExpanded: true,
    pdfPasswordEnabled: false,
    theme: null as 'light'|'dark'|null,
  }),
  actions: {
    setNoteExpandState({ noteId, isExpanded }: { noteId: string, isExpanded: boolean }) {
      this.noteExpandStates[noteId] = isExpanded;
    },
    setAllSpellcheckSettings(val: boolean) {
      this.reportingSpellcheckEnabled = val;
      this.projectNoteSpellcheckEnabled = val;
      this.userNoteSpellcheckEnabled = val;
      this.designSpellcheckEnabled = val;
      this.templateSpellcheckEnabled = val;
    },
  },
  getters: {
    isNoteExpanded() {
      return (noteId: string) => {
        const val = this.noteExpandStates[noteId];
        return val === undefined ? true : val;
      };
    },
  },
  persist: {
    storage: localStorage,
  }
})
