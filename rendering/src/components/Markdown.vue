<template>
  <div v-if="text" class="markdown">
    <component :is="{template: compiledMarkdown, data: () => $root}" />
  </div>
</template>

<script>
import { renderMarkdownToHtml } from 'reportcreator-markdown';
import 'highlight.js/styles/default.css';

export default {
  props: {
    text: {
      type: String,
      default: null,
    },
  },
  computed: {
    compiledMarkdown() {
      return renderMarkdownToHtml(this.text, { preview: false });
    },
  },
}
</script>

<style>
.code-block {
  white-space: pre-wrap;
}
.code-block code {
  display: block;
  width: 100%;
}
</style>
