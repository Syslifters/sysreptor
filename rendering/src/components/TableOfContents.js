import { h } from "vue";
import { v4 as uuidv4 } from "uuid";

export default {
  data: () => ({
    shouldRender: false,
    items: [],
  }),

  mounted() {
    // Defer rendering table of contents until everything else is rendered.
    // Then look in the DOM what should be included in the TOC
    this.$nextTick(() => {
      this.updateItems();
      this.$nextTick(() => {
        this.updateItems();
      })
    });
  },
  render() {
    if (!this.shouldRender) {
      return;
    }

    return h('div', this.$slots.default(this.items));
  },
  methods: {
    updateItems() {
      this.items = [];
      for (const el of this.$root.$el.querySelectorAll('.in-toc')) {
        if (!el.id) {
          el.setAttribute('id', uuidv4());
        }
        
        const attrs = Object.fromEntries(Array.from(el.attributes).map(a => [a.name, a.value]));
        this.items.push({
          id: el.id,
          href: '#' + el.id,
          title: attrs['data-toc-title'] || el.textContent,
          level: Number(attrs['data-toc-level'] || el.tagName.slice(1)) || 1,
          attrs: attrs,
        });
      }
      this.shouldRender = true;
    }
  }
}
