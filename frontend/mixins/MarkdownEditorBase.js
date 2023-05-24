import { EditorState } from '@codemirror/state';
import { EditorView, keymap, lineNumbers } from '@codemirror/view';
import { defaultKeymap, historyKeymap, indentWithTab, history } from '@codemirror/commands';
import { createEditorExtensionToggler } from 'reportcreator-markdown/editor/utils';
import { markdown } from 'reportcreator-markdown/editor/language.js';
import { spellcheck, spellcheckTheme } from 'reportcreator-markdown/editor/spellcheck.js';
import 'highlight.js/styles/default.css';
import { syntaxHighlighting, indentUnit } from '@codemirror/language';
import { forceLinting, setDiagnostics } from '@codemirror/lint';
import { markdownHighlightStyle, markdownHighlightCodeBlocks } from 'reportcreator-markdown/editor/highlight.js';

export default {
  props: {
    value: {
      type: String,
      default: '',
    },
    uploadFile: {
      type: Function,
      default: null,
    },
    rewriteFileUrl: {
      type: Function,
      default: null,
    },
    rewriteReferenceLink: {
      type: Function,
      default: null,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    lang: {
      type: String,
      default: null,
    }
  },
  emits: ['input'],
  data() {
    return {
      editorView: null,
      editorActions: {},
      fileUploadInProgress: false,
    };
  },
  computed: {
    valueNotNull() {
      return this.value || '';
    },
    editorMode() {
      return this.$store.state.settings.markdownEditorMode;
    },
    spellcheckEnabled() {
      return this.lang !== null && !this.disabled && 
        this.$store.state.settings.spellcheckEnabled && this.$store.getters['apisettings/settings'].features.spellcheck &&
        this.$store.getters['apisettings/settings'].languages.find(l => l.code === this.lang)?.spellcheck;
    },
  },
  watch: {
    value() {
      if (this.editorView && this.valueNotNull !== this.editorView.state.doc.toString()) {
        this.editorView.dispatch({
          changes: {
            from: 0,
            to: this.editorView.state.doc.length,
            insert: this.valueNotNull,
          }
        });
      }
    },
    disabled(val) {
      if (this.editorActions) {
        this.editorActions.disabled(val);
      }
    },
    lang(val) {
      if (this.spellcheckEnabled) {
        forceLinting(this.editorView);
      }
    },
    spellcheckEnabled(val) {
      this.editorActions.spellcheck(val);
      if (!val) {
        // clear existing spellcheck items from editor
        this.editorView.dispatch(setDiagnostics(this.editorView.state, []));
      }
    }
  },
  mounted() {
    this.initializeEditorView();
  },
  beforeDestroy() {
    if (this.editorView) {
      this.editorView.destroy();
    }
  },
  methods: {
    initializeEditorView() {
      this.editorView = new EditorView({
        parent: this.$refs.editor,
        state: EditorState.create({
          doc: this.valueNotNull,
          extensions: [
            lineNumbers(),
            history(),
            EditorState.allowMultipleSelections.of(true),
            EditorView.lineWrapping,
            EditorState.tabSize.of(4),
            indentUnit.of('    '),
            keymap.of([defaultKeymap, indentWithTab, historyKeymap]),
            markdown(),
            syntaxHighlighting(markdownHighlightStyle),
            markdownHighlightCodeBlocks,
            EditorView.updateListener.of((viewUpdate) => {
              // https://discuss.codemirror.net/t/codemirror-6-proper-way-to-listen-for-changes/2395/11
              if (viewUpdate.docChanged && viewUpdate.state.doc.toString() !== this.valueNotNull) {
                this.$emit('input', viewUpdate.state.doc.toString());
              }
            }),
            ...this.additionalCodeMirrorExtensions(),
          ]
        }),
      });

      this.editorActions = {
        disabled: createEditorExtensionToggler(this.editorView, [
          EditorView.editable.of(false),
          EditorState.readOnly.of(true),
        ]),
        spellcheck: createEditorExtensionToggler(this.editorView, [
          spellcheck({ performSpellcheckRequest: this.performSpellcheckRequest, performSpellcheckAddWordRequest: this.performSpellcheckAddWordRequest }),
          spellcheckTheme,
        ]),
        uploadFile: createEditorExtensionToggler(this.editorView, [
          EditorView.domEventHandlers({
            drop: (event, view) => {
              event.stopPropagation();
              event.preventDefault();
              const dropPos = this.editorView.posAtCoords({ x: event.clientX, y: event.clientY });
              this.uploadFiles(event.dataTransfer.files, dropPos);
            },
            paste: (event, view) => {
              if (event.clipboardData.files?.length > 0) {
                event.stopPropagation();
                event.preventDefault();
                this.uploadFiles(event.clipboardData.files);
              }
            }
          })
        ]),
      };
      this.editorActions.disabled(this.disabled);
      this.editorActions.spellcheck(this.spellcheckEnabled);
      this.editorActions.uploadFile(this.uploadFile !== null);
    },
    additionalCodeMirrorExtensions() {
      return [];
    },
    handleInput(val) {
      this.$emit('input', val);
    },
    handleBlur(val) {
      this.$emit('blur', val);
    },
    async uploadFiles(files, pos = null) {
      if (!this.uploadFile || !files || files.length === 0 || this.fileUploadInProgress) {
        return;
      }

      try {
        this.fileUploadInProgress = true;
        const results = await Promise.all(Array.from(files).map((file) => {
          try {
            return this.uploadFile(file);
          } catch (error) {
            this.$toast.global.requestError({ error, message: 'Failed to upload ' + file.name });
            return null;
          }
        }));

        const mdFileText = results.filter(u => u).join('\n');
        if (pos === null) {
          pos = this.editorView.state.selection.main.from;
        }
        this.editorView.dispatch({ changes: { from: pos, insert: mdFileText } });
      } finally {
        this.fileUploadInProgress = false;
      }
    },
    async performSpellcheckRequest(data) {
      if (!this.spellcheckEnabled || !data) {
        return {
          matches: []
        };
      }

      return await this.$axios.$post('/utils/spellcheck/', {
        ...data,
        language: this.lang,
      });
    },
    async performSpellcheckAddWordRequest(data) {
      try {
        return await this.$axios.$post('/utils/spellcheck/words/', data);
      } catch (error) {
        this.$toast.global.requestError({ error });
      }
    },
  }
}
