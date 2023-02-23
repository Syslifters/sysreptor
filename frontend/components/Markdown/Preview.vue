<template>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <div v-html="renderedMarkdown" class="preview" />
</template>

<script>
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
  },
  data() {
    return {
      renderedMarkdownRaw: '',
      imageCache: [],
    }
  },
  computed: {
    renderedMarkdown() {
      let html = this.renderedMarkdownRaw;
      for (const imgCacheEntry of this.imageCache) {
        if (imgCacheEntry.data) {
          html = html.replaceAll(imgCacheEntry.placeholder, imgCacheEntry.data)
        } else {
          html = html.replaceAll(imgCacheEntry.placeholder, '');
        }
      }
      return html;
    },
  },
  watch: {
    value() {
      this.updatePreview();
    },
    imageCache() {
      this.updatePreview();
    },
  },
  created() {
    this.updatePreview = throttle(this.renderMarkdown, 200);
    this.updatePreview();
  },
  methods: {
    renderMarkdown() {
      // Render markdown to HTML
      this.renderedMarkdownRaw = renderMarkdownToHtml(this.value || '', {
        to: 'html',
        preview: true,
        rewriteFileSource: this.rewriteFileSource,
      });
      // Clean up image cache: remove unused images to reduce memory usage
      for (const imgCacheEntry of this.imageCache) {
        if (!this.renderedMarkdownRaw.includes(imgCacheEntry.placeholder)) {
          this.imageCache = this.imageCache.filter(e => e !== imgCacheEntry);
        }
      }
    },
    async fetchImage(imgCacheEntry) {
      await this.$nextTick();
      
      try {
        const imgRes = await this.$axios.$get(imgCacheEntry.url, {
          responseType: 'arraybuffer'
        });
        const imageType = imgCacheEntry.url.toLowerCase().endsWith('.png') ? 'image/png' : 
            (imgCacheEntry.url.toLowerCase().endsWith('.jpg') || imgCacheEntry.url.toLowerCase().endsWith('.jpeg')) ? 'image/jpeg' :
              'image';
        const imgData = 'data:' + imageType + ';base64,' + Buffer.from(imgRes).toString('base64');
        imgCacheEntry.data = `src="${imgData}"`;
      } catch (error) {
        // remove from cache
        this.imageCache = this.imageCache.filter(e => e !== imgCacheEntry);
      }
    },
    rewriteFileSource(imgSrc) {
      // Rewrite image source to handle image fetching from markdown.
      // Images in markdown are referenced with a URL relative to the parent resource (e.g. "/images/name/image.png").
      // Images require API authentication (JWT Tokens), which cannot be done using just HTML.
      // Fetch API images with authentication and cache them. 
      // Fetching is handled async to not block the rendering process and replaced with data-URLs in the HTML in a post-processing step.
      // The post-processing step is required, because the Markdown rendering is not reactive. Image cache changes do not trigger re-rendering.
      if (!this.rewriteFileUrl || !imgSrc.startsWith('/')) {
        return imgSrc;
      }

      const apiUrl = this.rewriteFileUrl(imgSrc);
      if (imgSrc.startsWith('/files/')) {
        imgSrc = absoluteApiUrl(apiUrl, this.$axios);
      } else if (!this.imageCache.some(e => e.url === apiUrl)) {
        const imgCacheEntry = {
          url: apiUrl,
          placeholder: `src="${imgSrc}"`,
          data: null,
        };
        this.imageCache.push(imgCacheEntry);
        this.fetchImage(imgCacheEntry);
      }
      
      return imgSrc;
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

:deep() {
  h1, h2, h3, h4, h5, h6 {
    font-weight: bold;
  }
  h1 { font-size: 2em; }
  h2 { font-size: 1.75em; }
  h3 { font-size: 1.5em; }
  h4 { font-size: 1.25em; }
  h5 { font-size: 1.1em; }
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

  ul, ol {
    padding: 0;
    margin: 0;

    li {
      margin-left: 1.5em;
      padding-left: 0;
    }

    li.task-list-item {
      list-style-type: none;

      input[type=checkbox] {
        margin-left: -1.5em;
        width: 1.5em;
        padding: 0;
      }
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

}
</style>
