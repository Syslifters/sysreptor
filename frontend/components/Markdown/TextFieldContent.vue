<template>
  <div class="mde-text-field-wrapper">
    <div ref="editor" class="mde-text-field" :class="{disabled: disabled}" />
  </div>
</template>

<script>
import { EditorState, EditorSelection } from '@codemirror/state';
import { EditorView, tooltips } from '@codemirror/view';
import { history } from '@codemirror/commands';
import { forceLinting, setDiagnostics } from '@codemirror/lint';
import { createEditorExtensionToggler } from 'reportcreator-markdown/editor/utils';
import { spellcheck, spellcheckTheme } from 'reportcreator-markdown/editor/spellcheck.js';
import { highlightTodos } from 'reportcreator-markdown/editor/todos';

export default {
  props: {
    value: {
      type: String,
      default: null,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    lang: {
      type: String,
      default: null,
    },
    spellcheckSupported: {
      type: Boolean,
      default: false,
    }
  },
  emits: ['input'],
  data() {
    return {
      editorView: null,
      editorActions: {},
    };
  },
  computed: {
    valueNotNull() {
      return this.value || '';
    },
    spellcheckEnabled() {
      return this.lang !== null && !this.disabled && this.spellcheckSupported && 
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
    this.editorView = new EditorView({
      parent: this.$refs.editor,
      state: EditorState.create({
        doc: this.valueNotNull,
        extensions: [
          history(),
          highlightTodos,
          tooltips({ parent: document.body }),
          // Prevent newlines
          EditorState.transactionFilter.of((tr) => {
            const changesWithoutNewlines = [];
            let transactionModified = false;
            tr.changes.iterChanges((from, to, fromB, toB, insert) => {
              if (insert.text.length > 1) {
                insert = insert.text.join('');
                transactionModified = true;
              }
              changesWithoutNewlines.push({ from, to, insert })
            });
            
            return transactionModified ? { 
              annotations: tr.annotations,
              effects: tr.effects,
              scrollIntoView: tr.scrollIntoView,
              changes: changesWithoutNewlines,
            } : tr;
          }),
          EditorView.domEventHandlers({
            blur: event => this.$emit('blur', event),
            focus: event => this.$emit('focus', event),
          }),
          EditorView.updateListener.of((viewUpdate) => {
            // https://discuss.codemirror.net/t/codemirror-6-proper-way-to-listen-for-changes/2395/11
            if (viewUpdate.docChanged && viewUpdate.state.doc.toString() !== this.valueNotNull) {
              this.$emit('input', viewUpdate.state.doc.toString());
            }
          }),
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
    };
    this.editorActions.disabled(this.disabled);
    this.editorActions.spellcheck(this.spellcheckEnabled);
  },
  beforeDestroy() {
    if (this.editorView) {
      this.editorView.destroy();
    }
  },
  methods: {
    async performSpellcheckRequest(data) {
      if (!this.lang) {
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
  },
}
</script>

<style lang="scss" scoped>

.mde-text-field, .mde-text-field-wrapper {
  width: 100%;
  max-width: 100%;
  display: inline-block;
  color: map-deep-get($material-theme, 'text', 'primary');
}

.mde-text-field.disabled {
  color: map-deep-get($material-theme, 'text', 'disabled');
}

:deep(.mde-text-field) {
  .cm-focused {
    outline: none !important;
  }

  .cm-content {
    font-family: $body-font-family;
  }

  .tok-todo {
    background-color: $risk-color-critical;
    color: white;
    padding-left: 0.2em;
    padding-right: 0.2em;
    border-radius: 10%;
  }

  // Hide scrollbar
  .cm-scroller {
    overflow: hidden;
  }
}
</style>
