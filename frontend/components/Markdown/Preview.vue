<template>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <div v-html="renderedMarkdown" class="preview" />
</template>

<script>
import { v4 as uuidv4 } from 'uuid';
import { throttle } from 'lodash';
import { renderMarkdownToHtml } from 'reportcreator-markdown';
import { absoluteApiUrl } from '~/utils/urls';

export default {
  props: {
    value: {
      type: String,
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
  },
  data() {
    return {
      renderedMarkdown: '',
      cachebuster: uuidv4(),
    }
  },
  watch: {
    value() {
      this.updatePreview();
    },
  },
  created() {
    this.updatePreview = throttle(this.renderMarkdown, 200);
    this.updatePreview();
  },
  updated() {
    // Prevent navigation when clicking on anchor links in preview
    this.$el.querySelectorAll('.preview a[href^="#"]').forEach((a) => {
      a.addEventListener('click', (e) => {
        e.preventDefault();
        const target = document.querySelector(a.getAttribute('href'));
        if (target) {
          target.scrollIntoView({ behavior: 'smooth' });
        }
      });
    });
  },
  methods: {
    renderMarkdown() {
      // Render markdown to HTML
      this.renderedMarkdown = renderMarkdownToHtml(this.value || '', {
        preview: true,
        rewriteFileSource: this.rewriteFileSource,
        rewriteReferenceLink: this.rewriteReferenceLink,
      });
    },
    rewriteFileSource(imgSrc) {
      // Rewrite image source to handle image fetching from markdown.
      // Images in markdown are referenced with a URL relative to the parent resource (e.g. "/images/name/image.png").
      if (!this.rewriteFileUrl || !imgSrc.startsWith('/')) {
        return imgSrc;
      }

      return absoluteApiUrl(this.rewriteFileUrl(`${imgSrc}?c=${this.cachebuster}`), this.$axios);
    },
  },
}
</script>

<style lang="scss" scoped>
.preview {
  overflow: auto;
  word-wrap: break-word;
  background-color: #fafafa;
}

.preview > :deep(*:first-child) {
  margin-top: 0;
}

.preview :deep() {
  @import "~assets/rendering/base-text.scss";

  .footnotes {
    border-top: 1px solid black;
    margin-top: 2em;

    h4 {
      font-size: 1em;
    }
    .data-footnote-backref {
      display: none;
    }
  }

  .file-download-preview {
    text-align: center;
    font-size: inherit;
    text-decoration: none;

    &::before {
      font-size: 20pt;
    }
  }

  .ref {
    color: inherit;
    font-style: inherit;
    text-decoration: underline;
  }
}
</style>
