<template>
  <div v-if="text" class="markdown" v-html="compiledMarkdown"></div>
</template>

<script>
import { getMarkdownRenderer } from '@/markdown.js';
const md = getMarkdownRenderer();

export default {
  props: {
    text: {
      type: String,
      default: null,
    },
  },
  computed: {
    compiledMarkdown() {
      return md.render(this.text);
    }
  },
}
</script>

<style>
.code-block {
  white-space: pre-wrap;
}
.code-block code {
  display: inline-block;
  width: 100%;
}
</style>
