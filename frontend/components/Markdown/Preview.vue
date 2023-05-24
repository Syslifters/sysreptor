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
    rewriteReferenceLink: {
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
  updated() {
    // Prevent navigation when clicking on links in preview
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
      this.renderedMarkdownRaw = renderMarkdownToHtml(this.value || '', {
        preview: true,
        rewriteFileSource: this.rewriteFileSource,
        rewriteReferenceLink: this.rewriteReferenceLink,
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
        if (error?.response?.status === 404) {
          imgCacheEntry.data = '';
        } else {
          this.imageCache = this.imageCache.filter(e => e !== imgCacheEntry);
        }
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
