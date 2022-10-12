<template>
  <div class="mde">
    <v-toolbar dense flat class="toolbar">
      <markdown-toolbar-button @click="toggleStrong" title="Bold" icon="mdi-format-bold" :disabled="disabled" :active="isTypeInSelection('strong')" />
      <markdown-toolbar-button @click="toggleEmphasis" title="Italic" icon="mdi-format-italic" :disabled="disabled" :active="isTypeInSelection('emphasis')" />
      <markdown-toolbar-button @click="toggleStrikethrough" title="Strikethrough" icon="mdi-format-strikethrough" :disabled="disabled" :active="isTypeInSelection('strikethrough')" />
      <span class="separator" />
      <markdown-toolbar-button @click="toggleListUnordered" title="Bullet List" icon="mdi-format-list-bulleted" :disabled="disabled" :active="isTypeInSelection('listUnordered')" />
      <markdown-toolbar-button @click="toggleListOrdered" title="Numbered List" icon="mdi-format-list-numbered" :disabled="disabled" :active="isTypeInSelection('listOrdered')" />
      <markdown-toolbar-button @click="insertCodeBlock" title="Code" icon="mdi-code-tags" :disabled="disabled" :active="isTypeInSelection('codeFenced')" />
      <markdown-toolbar-button @click="insertTable" title="Table" icon="mdi-table" :disabled="disabled" :active="isTypeInSelection('table')" />
      <span class="separator" />
      <markdown-toolbar-button @click="toggleLink" title="Link" icon="mdi-link" :disabled="disabled" :active="isTypeInSelection('link')" />
      <template v-if="uploadImage">
        <markdown-toolbar-button @click="$refs.fileInput.click()" title="Image" icon="mdi-image" :disabled="disabled || imageUploadInProgress" />
        <input ref="fileInput" type="file" multiple @change="uploadImages($event.target.files)" :disabled="disabled || imageUploadInProgress" class="d-none" />
      </template>
      <span class="separator" />
      <markdown-toolbar-button @click="spellcheckEnabled = !spellcheckEnabled" title="Spellcheck" icon="mdi-spellcheck" :disabled="disabled" :active="spellcheckEnabled" />
      <span class="separator" />
      <markdown-toolbar-button @click="undo" title="Undo" icon="mdi-undo" :disabled="disabled || !canUndo" />
      <markdown-toolbar-button @click="redo" title="Redo" icon="mdi-redo" :disabled="disabled || !canRedo" />
      <span class="separator" />
      <markdown-toolbar-button v-if="editorMode === 'markdown'" @click="editorMode = 'markdown-preview'" title="Markdown" icon="mdi-language-markdown" :active="true" />
      <markdown-toolbar-button v-else-if="editorMode === 'markdown-preview'" @click="editorMode = 'preview'" title="Side-by-Side View" icon="mdi-view-split-vertical" :active="true" />
      <markdown-toolbar-button v-else-if="editorMode === 'preview'" @click="editorMode = 'markdown'" title="Preview" icon="mdi-image-filter-hdr" :active="true" />
    </v-toolbar>
    <v-divider />

    <v-row no-gutters>
      <v-col :cols="editorMode === 'markdown-preview' ? 6 : null" v-show="editorMode !== 'preview'">
        <div
          ref="editor" 
          class="mde-editor" 
          :class="{'mde-editor-side': editorMode === 'markdown-preview'}"
        />
      </v-col>
      <v-col v-if="editorMode === 'markdown-preview'">
        <v-divider vertical />
      </v-col>
      <v-col :cols="editorMode === 'markdown-preview' ? 6 : null" v-if="editorMode !== 'markdown'">
        <!-- eslint-disable-next-line vue/no-v-html -->
        <div class="preview" v-html="renderedMarkdown" />
      </v-col>
    </v-row>
    <v-divider />

    <div class="mde-statusbar">
      <template v-if="uploadImage">
        <span v-if="!imageUploadInProgress">Attach files by drag and dropping or pasting from clipboard.</span>
        <span v-else>Upload in progress...</span>
      </template>
      <span>lines: {{ lineCount }}</span>
      <span>words: {{ wordCount }}</span>
      <span>{{ currentLineNumber }}:{{ currentColNumber }}</span>
    </div>
  </div>
</template>

<script>
import { Compartment, EditorState, StateEffect } from '@codemirror/state';
import { crosshairCursor, drawSelection, EditorView, keymap, lineNumbers, rectangularSelection } from '@codemirror/view';
import { defaultKeymap, historyKeymap, indentWithTab, history, undo, redo, undoDepth, redoDepth } from '@codemirror/commands';
import urlJoin from 'url-join';
import { renderMarkdownToHtml } from 'reportcreator-markdown';
import { markdown } from 'reportcreator-markdown/editor/language.js';
import { spellcheck, spellcheckTheme } from 'reportcreator-markdown/editor/spellcheck.js';
import { isTypeInSelection, toggleStrong, toggleEmphasis, toggleStrikethrough, toggleListUnordered, toggleListOrdered, toggleLink, insertCodeBlock, insertTable } from 'reportcreator-markdown/editor/commands.js';
import 'highlight.js/styles/default.css';
import { syntaxHighlighting } from '@codemirror/language';
import { forceLinting, setDiagnostics } from '@codemirror/lint';
import { markdownHighlightStyle, markdownHighlightCodeBlocks } from 'reportcreator-markdown/editor/highlight.js';
import { throttle } from 'lodash';
import { absoluteApiUrl } from '@/utils/urls';

function createEditorCompartment(view) {
  const compartment = new Compartment();
  const run = (extension) => {
    compartment.get(view.state)
      ? view.dispatch({ effects: compartment.reconfigure(extension) }) // reconfigure
      : view.dispatch({ effects: StateEffect.appendConfig.of(compartment.of(extension)) }) // inject
  }
  return { compartment, run }
}

function createEditorExtensionToggler(view, extension) {
  const { compartment, run } = createEditorCompartment(view)
  return (targetApply) => {
    const exExtension = compartment.get(view.state)
    const apply = targetApply ?? exExtension !== extension
    run(apply ? extension : [])
  }
}

export default {
  props: {
    value: {
      type: String,
      default: '',
    },
    uploadImage: {
      type: Function,
      default: null,
    },
    imageUrlsRelativeTo: {
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
    }
  },
  emits: ['input'],
  data() {
    return {
      editorView: null,
      editorActions: {},
      imageUploadInProgress: false,
      renderedMarkdown: '',
    };
  },
  computed: {
    valueNotNull() {
      return this.value || '';
    },
    editorMode: {
      get() {
        return this.$store.state.settings.markdownEditorMode;
      },
      set(val) {
        this.$store.commit('settings/updateMarkdownEditorMode', val);
      },
    },
    spellcheckEnabled: {
      get() {
        return this.$store.state.settings.spellcheckEnabled;
      },
      set(val) {
        this.$store.commit('settings/updateSpellcheckEnabled', val);
      }
    },
    canUndo() {
      if (this.editorView) {
        return undoDepth(this.editorView.state);
      }
      return false;
    },
    canRedo() {
      if (this.editorView) {
        return redoDepth(this.editorView.state);
      }
      return false;
    },
    currentLineNumber() {
      if (this.editorView) {
        return this.editorView.state.doc.lineAt(this.editorView.state.selection.main.head).number;
      }
      return 1;
    },
    currentColNumber() {
      if (this.editorView) {
        const pos = this.editorView.state.selection.main.head
        const line = this.editorView.state.doc.lineAt(pos);
        return pos - line.from;
      }
      return 1;
    },
    lineCount() {
      if (this.editorView) {
        return this.editorView.state.doc.lines;
      }
      return 1;
    },
    wordCount() {
      const pattern = /[a-zA-Z0-9_\u00A0-\u02AF\u0392-\u03C9\u0410-\u04F9]+|[\u4E00-\u9FFF\u3400-\u4DBF\uF900-\uFAFF\u3040-\u309F\uAC00-\uD7AF]+/g;
      const m = (this.valueNotNull).match(pattern);
      let count = 0;
      if (m === null) { return count; }
      for (let i = 0; i < m.length; i++) {
        if (m[i].charCodeAt(0) >= 0x4E00) {
          count += m[i].length;
        } else {
          count += 1;
        }
      }
      return count;
    },
  },
  watch: {
    value: {
      handler() {
        this.renderMarkdown();
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
      immediate: true,
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
          lineNumbers(),
          history(),
          EditorState.allowMultipleSelections.of(true),
          drawSelection(),
          rectangularSelection(),
          crosshairCursor(),
          EditorState.tabSize.of(4),
          EditorView.lineWrapping,
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
        ]
      }),
    });
    // console.log(this.editorView, this);
    this.editorActions = {
      disabled: createEditorExtensionToggler(this.editorView, [
        EditorView.editable.of(false),
        EditorState.readOnly.of(true),
      ]),
      spellcheck: createEditorExtensionToggler(this.editorView, [
        spellcheck(this.performSpellcheckRequest),
        spellcheckTheme,
      ]),
      uploadImage: createEditorExtensionToggler(this.editorView, [
        EditorView.domEventHandlers({
          drop: (event, view) => {
            event.stopPropagation();
            event.preventDefault();
            this.uploadImages(event.dataTransfer.files);
          },
          paste: (event, view) => {
            if (event.clipboardData.files?.length > 0) {
              event.stopPropagation();
              event.preventDefault();
              this.uploadImages(event.clipboardData.files);
            }
          }
        })
      ])
    };
    this.editorActions.disabled(this.disabled);
    this.editorActions.spellcheck(this.spellcheckEnabled);
    this.editorActions.uploadImage(this.uploadImage !== null);
  },
  beforeDestroy() {
    if (this.editorView) {
      this.editorView.destroy();
    }
  },
  methods: {
    handleInput(val) {
      this.$emit('input', val);
    },
    handleBlur(val) {
      this.$emit('blur', val);
    },
    renderMarkdown: throttle(function() {
      this.renderedMarkdown = renderMarkdownToHtml(this.valueNotNull, {
        to: 'html',
        preview: true,
        rewriteImageSource: this.rewriteImageSource,
      });
    }, 100),
    async uploadImages(files) {
      if (!this.uploadImage || !files || files.length === 0 || this.imageUploadInProgress) {
        return;
      }

      this.imageUploadInProgress = true;
      const imageUrls = await Promise.all(Array.from(files).map((file) => {
        try {
          return this.uploadImage(file);
        } catch (error) {
          this.$toast.global.requestError({ error, message: 'Failed to upload ' + file.name });
          return null;
        }
      }));

      const mdImageText = imageUrls.filter(u => u).map(u => `![](${u})`).join('\n');
      this.editorView.dispatch({ changes: { from: this.editorView.state.selection.main.from, insert: mdImageText } });

      this.imageUploadInProgress = false;
      this.$refs.fileInput.files = null;
    },
    rewriteImageSource(imgSrc) {
      // TODO: download images from API with authentication (removes requirement for images to be available unauthenticated)
      if (!this.imageUrlsRelativeTo) {
        return imgSrc;
      }

      if (['http', 'data'].some(p => imgSrc.startsWith(p)) || imgSrc.startsWith('/api/')) {
        return absoluteApiUrl(imgSrc, this.$axios);
      } else {
        return absoluteApiUrl(urlJoin(this.imageUrlsRelativeTo, imgSrc), this.$axios);
      }
    },
    async performSpellcheckRequest(data) {
      return await this.$axios.$post('/utils/spellcheck/', {
        ...data,
        language: this.lang,
      });
    },
    ...Object.fromEntries(Object.entries({
      undo,
      redo,
      toggleStrong,
      toggleEmphasis,
      toggleStrikethrough,
      toggleListUnordered,
      toggleListOrdered,
      toggleLink,
      insertCodeBlock,
      insertTable,
    })
      .map(([n, fn]) => [n, function() { 
        if (!this.editorView) {
          return false;
        }

        try {
          return fn({ state: this.editorView.state, dispatch: this.editorView.dispatch }); 
        } catch (err) {
          // eslint-disable-next-line no-console
          console.error('Error in CodeMirror action', err);
        }
      }])),
    isTypeInSelection(type) {
      if (!this.editorView) {
        return false;
      }
      return isTypeInSelection(this.editorView.state, type);
    }
  }
}
</script>

<style lang="scss" scoped>
$mde-min-height: 15em;

.toolbar {
  background-color: inherit !important;
}

.separator {
  display: inline-block;
  height: 1.5em;
  width: 0;
  border-left: 1px solid #d9d9d9;
  border-right: 1px solid #fff;
  color: transparent;
  text-indent: -10px;
  margin: 0 0.5em;
}

.mde-editor {
  display: contents;

  &-side.cm-editor {
    width: 50%;
  }
}

.preview {
  height: 100%;
  min-height: $mde-min-height;

  background-color: #fafafa;
  padding: 0.5em;
  overflow: auto;
  word-wrap: break-word;

  &-side {
    width: 50%;
  }
}

.mde-statusbar {
  font-size: smaller;
  text-align: right;
  padding: 0.3em 1em;
  color: #959694;

  span {
    display: inline-block;
    min-width: 4em;
    margin-left: 1em;
  }
}

:deep(.mde-editor) {
  /* set min-height, grow when lines overflow */
  .cm-content, .cm-gutter { min-height: $mde-min-height; }
  .cm-gutters { margin: 1px; }
  .cm-scroller { overflow: auto; }
  .cm-wrap { border: 1px solid silver }
}

:deep(.mde-editor) {
  /* inline markdown styles */
  .cm-content {
    font-family: $body-font-family;

    .tok-h1, .tok-h2, .tok-h3, .tok-h4, .tok-h5, .tok-h6 {
      font-weight: bold;
    }
    .tok-h1 { font-size: 3em; }
    .tok-h2 { font-size: 2.5em; }
    .tok-h3 { font-size: 2em; }
    .tok-h4 { font-size: 1.5em; }
    .tok-h5 { font-size: 1.25em; }
    .tok-h6 { font-size: 1em; }

    .tok-strong { font-weight: bold }
    .tok-emphasis { font-style: italic; }
    .tok-strikethrough { text-decoration: line-through;}

    .tok-codeblock, .tok-inlinecode {
      font-family: monospace;
      background-color: map-deep-get($material-light, 'code', 'background');
      color: map-deep-get($material-light, 'code', 'color');
    }
    .tok-inlinecode {
      padding: $code-padding;
    }

    .tok-table {
      font-family: monospace;
    }

    .tok-footnote {
      vertical-align: super;
      font-size: 0.9em;
    }

    .tok-link, .tok-image, .tok-footnote {
      color: #7f8c8d;
    }
    .tok-url {
      color: #aab2b3;
      text-decoration: underline;
    }

    .tok-quote {
      color: #7f8c8d;
    }

    // HTML tag highlighting
    .tok-tagname, .tok-anglebracket, .tok-attributename, .tok-attributevalue, .tok-comment { font-family: monospace; }
    .tok-tagname, .tok-anglebracket { color: #085; }
    .tok-attributename { color: #795da3; }
    .tok-attributevalue { color:  #a11; }
    .tok-comment { color: #940; }

  }
}

/* Preview styles */
:deep(.preview) {
    h1, h2, h3, h4, h5, h6 {
      font-weight: bold;
    }
    h1 { font-size: 3em; }
    h2 { font-size: 2.5em; }
    h3 { font-size: 2em; }
    h4 { font-size: 1.5em; }
    h5 { font-size: 1.25em; }
    h6 { font-size: 1em; }

  .code-block {
    white-space: pre-wrap;
    code {
      display: block;
    }
  }

  .footnotes {
    border-top: 1px solid black;
    margin-top: 2em;
  }

  table {
    caption-side: bottom;
    width: 100%;
  }
  table, th, td {
    border: 1px solid black;
    border-collapse: collapse;
  }
  th, td {
    padding: 5px;
  }

  figure {
    text-align: center;
  }
  img {
    max-width: 100%;
  }

  figcaption, caption {
    font-weight: bold;
  }

  .footnotes {
    h4 {
      font-size: 1em;
    }
    .data-footnote-backref {
      display: none;
    }
  }
}
</style>
