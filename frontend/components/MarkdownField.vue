<template>
  <div class="vue-easymde" :class="{'disabled': disabled}">
    <textarea
      class="vue-easymde-textarea"
      :value="value"
      @input="handleInput($event.target.value)"
    />
  </div>
</template>

<script>
import EasyMDE from 'easymde';
import urlJoin from 'url-join';
import { debounce } from 'lodash';
import DOMPurify from 'dompurify';
import { getMarkdownRenderer, popAttr } from '../../rendering/src/markdown.js';
import 'highlight.js/styles/default.css';
import { absoluteApiUrl } from '@/utils/urls';

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
    }
  },
  emits: ['input'],
  data() {
    const md = getMarkdownRenderer(true).use(this.rewriteImageSourcePlugin);

    const attrDisabled = this.disabled ? { disabled: 'disabled' } : {};

    return {
      easymde: null,
      editorConfigs: {
        autoDownloadFontAwesome: false,
        autofocus: false,
        autosave: { enabled: false },
        spellChecker: false,
        nativeSpellcheck: false,
        lineNumbers: false,
        sideBySideFullscreen: false,
        uploadImage: true,
        imageUploadFunction: this.uploadImageWrapper,
        // TODO: support attrlist for image preview in editor; toggle previewImagesInEditor
        // previewImagesInEditor: true,
        // overlayMode: { mode: null },
        imagesPreviewHandler: this.rewriteImageSource,
        previewRender: text => DOMPurify.sanitize(md.render(text), { ADD_TAGS: ['footnote'] }),
        errorCallback: errorMessage => this.$toast.error(errorMessage),
        toolbar: [
          {
            name: "bold",
            action: EasyMDE.toggleBold,
            className: "mdi mdi-format-bold",
            title: "Bold",
            attributes: attrDisabled,
          },
          {
            name: "italic",
            action: EasyMDE.toggleItalic,
            className: "mdi mdi-format-italic",
            title: "Italic",
            attributes: attrDisabled,
          },
          {
            name: 'strikethrough',
            action: EasyMDE.toggleStrikethrough,
            className: 'mdi mdi-format-strikethrough',
            title: 'Strikethrough',
            attributes: attrDisabled,
          },
          '|',
          {
            name: 'unordered-list',
            action: EasyMDE.toggleUnorderedList,
            className: 'mdi mdi-format-list-bulleted',
            title: 'Generic List',
            attributes: attrDisabled,
          },
          {
            name: 'ordered-list',
            action: EasyMDE.toggleOrderedList,
            className: 'mdi mdi-format-list-numbered',
            title: 'Numbered List',
            attributes: attrDisabled,
          },
          {
            name: 'code',
            action: EasyMDE.toggleCodeBlock,
            className: 'mdi mdi-code-tags',
            title: 'Code',
            attributes: attrDisabled,
          },
          {
            name: 'table',
            action: EasyMDE.drawTable,
            className: 'mdi mdi-table',
            title: 'Table',
            attributes: attrDisabled,
          },
          '|',
          {
            name: 'link',
            action: EasyMDE.drawLink,
            className: 'mdi mdi-link',
            title: 'Link',
            attributes: attrDisabled,
          },
          ...((this.uploadImage !== null) ? [{
            name: 'upload-image',
            action: EasyMDE.drawUploadedImage,
            className: 'mdi mdi-image',
            title: 'Image upload',
            attributes: attrDisabled,
          }] : []),
          '|',
          {
            name: 'undo',
            action: EasyMDE.undo,
            className: 'mdi mdi-undo',
            noDisable: true,
            title: 'Undo',
            attributes: attrDisabled,
          },
          {
            name: 'redo',
            action: EasyMDE.redo,
            className: 'mdi mdi-redo',
            noDisable: true,
            title: 'Redo',
            attributes: attrDisabled,
          },
          '|',
          {
            name: 'preview',
            action: () => { this.easymde.togglePreview(); this.updateEditorModeFromEditor(); },
            className: 'mdi mdi-image-filter-hdr',
            noDisable: true,
            title: 'Preview',
            default: true,
          },
          {
            name: 'side-by-side',
            action: () => { this.easymde.toggleSideBySide(); this.updateEditorModeFromEditor(); },
            className: 'mdi mdi-view-split-vertical',
            noDisable: true,
            noMobile: true,
            title: 'Side by Side',
            default: true,
          },
        ],
        shortcuts: {
          toggleFullScreen: null,
          toggleSideBySide: null,
          togglePreview: null,
        },
      }
    }
  },
  computed: {
    editorMode: {
      get() {
        return this.$store.state.settings.markdownEditorMode;
      },
      set(val) {
        this.$store.commit('settings/updateMarkdownEditorMode', val);
      },
    }
  },
  watch: {
    value(val) {
      if (val !== this.easymde.value()) {
        this.easymde.value(val);
      }
    },
    editorMode(val) {
      // Synchronize editorMode between EasyMDE and store
      this.setEditorModeInEditor(val);
    },
    disabled(val) {
      this.easymde.codemirror.setOption('readOnly', val);
    }
  },
  created() {
    this.updateEditorModeFromEditor = debounce(this.updateEditorModeFromEditor, 10);
  },
  mounted() {
    const configs = Object.assign({
      element: this.$el.firstElementChild,
      initialValue: this.modelValue || this.value,
    }, this.editorConfigs);
      // Synchronize the value of modelValue and initialValue
    if (configs.initialValue) {
      this.$emit('input', configs.initialValue);
    }

    this.easymde = new EasyMDE(configs);
    this.setEditorModeInEditor(this.editorMode);

    if (this.disabled) {
      this.easymde.codemirror.setOption('readOnly', true);
    }

    // Bind events
    this.easymde.codemirror.on('change', (instance, changeObj) => {
      if (changeObj.origin === 'setValue') {
        return;
      }
      const val = this.easymde.value();
      this.handleInput(val);
    });
    this.easymde.codemirror.on('blur', () => {
      const val = this.easymde.value();
      this.handleBlur(val);
    });
  },
  deactivated() {
    if (!this.easymde) {
      return;
    }
    if (this.easymde.codemirror.getOption('fullScreen')) {
      this.easymde.toggleFullScreen();
    }
  },
  destroyed() {
    this.easymde = null;
  },
  methods: {
    handleInput(val) {
      this.$emit('input', val);
    },
    handleBlur(val) {
      this.$emit('blur', val);
    },
    setEditorModeInEditor(mode) {
      if (!this.easymde) {
        return;   
      }

      if (mode === 'preview' && !this.easymde.isPreviewActive()) {
        this.easymde.togglePreview();
      } else if (mode === 'markdown-preview' && !this.easymde.isSideBySideActive()) {
        this.easymde.toggleSideBySide();
      } else if (mode === 'markdown') {
        if (this.easymde.isPreviewActive()) {
          this.easymde.togglePreview();
        }
        if (this.easymde.isSideBySideActive()) {
          this.easymde.toggleSideBySide();
        }
      }
    },
    updateEditorModeFromEditor() {
      let mode = 'markdown';
      if (this.easymde.isPreviewActive()) {
        mode = 'preview';
      } else if (this.easymde.isSideBySideActive()) {
        mode = 'markdown-preview';
      }
      this.editorMode = mode;
    },
    uploadImageWrapper(file, onSuccess, onError) {
      if (this.uploadImage === null) {
        onError('Image uploaded not supported');
      }

      this.uploadImage(file)
        .then(onSuccess)
        .catch(() => {
          onError('Failed to upload image')
        });
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
    rewriteImageSourcePlugin(md) {
      const defaultImageRenderer = md.renderer.rules.image;
      md.renderer.rules.image = (tokens, idx, options, env, self) => {
        for (const t of tokens) {
          if (t.type === 'image') {
            const src = popAttr(t.attrs, 'src') || '';
            t.attrs.push(['src', this.rewriteImageSource(src)]);
          }
        }
        return defaultImageRenderer(tokens, idx, options, env, self);
      };
    },
  }
}
</script>

<style lang="scss">
@import '../node_modules/easymde/dist/easymde.min.css';
.vue-easymde {
  .markdown-body {
    padding: 0.5em
  }
  img {
    max-width: 100%;
  }
  .editor-preview-active, &.editor-preview-active-side {
    display: block;
  }
  .editor-preview-side {
    z-index: initial;
  }
  /* Improved code block preview styling */
  pre > span > .cm-comment:not(.cm-formatting-code):only-child {
    display: inline-block;
    width: 100%;
  }
  table {
    caption-side: bottom;
  }
}

.editor-preview {
  figure {
    text-align: center;
  }
  .code-block code {
    display: inline-block;
    width: 100%;
  }
}

.vue-easymde.disabled {
  button[disabled] {
    cursor: default;
    color: gray;

    &:hover {
      border-color: transparent;
      background: white;
    }
  }

  .CodeMirror {
    color: gray;
  }
}

</style>
