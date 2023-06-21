<script>
import { defineComponent, h } from 'vue';
import { renderMarkdownToHtml } from 'reportcreator-markdown';
import 'highlight.js/styles/default.css';


export default {
  name: 'markdown',
  props: {
    text: {
      type: String,
      default: null,
    },
  },
  methods: {
    compileMarkdown(text) {
      return renderMarkdownToHtml(text, { preview: false });
    },
  },
  render() {
    let mdText = this.text;
    if (!mdText && this.$slots.default) {
      // Slot content is always raw text because of templateCompilerOptions.getTextMode
      mdText = this.$slots.default().map(vnode => vnode.children).join('');
    }
    return h('div', { class: 'markdown' }, [
      h(defineComponent({
        name: 'markdown-content',
        data: () => this.$root,
        components: this.$root.$options.components,
        ...(mdText ? 
          { template: this.compileMarkdown(mdText) } : 
          { render: () => [] }
        ),
      })),
    ]);
  }
}
</script>

<style>
.code-block {
  white-space: pre-wrap;
}
.code-block code {
  display: block;
}
</style>