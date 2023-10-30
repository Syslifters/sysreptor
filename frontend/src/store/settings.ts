import { MarkdownEditorMode } from "~/utils/types";

export const useLocalSettings = defineStore('settings', {
  state: () => ({
    autoSaveEnabled: true,
    markdownEditorMode: MarkdownEditorMode.MARKDOWN as MarkdownEditorMode,
    spellcheckEnabled: true,
    reportInputMenuSize: 15,
    templateInputMenuSize: 15,
    notebookInputMenuSize: 15,
    reportFieldDefinitionMenuSize: 15,
    findingFieldDefinitionMenuSize: 15,
    templateFieldFilterDesign: 'all',
    templateFieldFilterHiddenFields: [] as string[],
    noteExpandStates: {} as {[noteId: string]: boolean},
  }),
  actions: {
    setNoteExpandState({ noteId, isExpanded }: { noteId: string, isExpanded: boolean }) {
      this.noteExpandStates[noteId] = isExpanded;
    },
  },
  getters: {
    isNoteExpanded() {
      return (noteId: string) => {
        const val = this.noteExpandStates[noteId];
        return val === undefined ? true : val;
      };
    },
    spellcheckLanguageToolEnabled() {
      const apiSettings = useApiSettings();
      return (lang: string|null) => {
        return lang !== null &&
            this.spellcheckEnabled &&
            apiSettings.settings!.features.spellcheck &&
            Boolean(apiSettings.settings!.languages.find(l => l.code === lang)?.spellcheck || lang === 'auto');
      }
    },
    spellcheckBrowserEnabled() {
      const apiSettings = useApiSettings();
      return (lang: string|null) => {
        return lang !== null &&
            this.spellcheckEnabled &&
            !apiSettings.settings!.features.spellcheck;
      }
    },
  },
  persist: {
    storage: persistedState.localStorage,
  }
})
