<script>
import { h } from "vue";
import { v4 as uuidv4 } from "uuid";
import { callForTicks } from "../utils";

export default {
  props: {
    to: {
      type: String,
      required: true
    },
  },
  data() {
    return {
      refEl: null,
      error: null,
    };
  },
  computed: {
    toId() {
      return this.to.startsWith('#') ? this.to.substring(1) : this.to;
    }
  },
  async mounted() {
    await callForTicks(4, this.$nextTick, () => this.updateReference());
    if (this.error) {
      console.warn(this.error.message, this.error);
    }
  },
  render() {
    const refClasses = ['ref'];
    let title = [];
    if (this.$slots.default) {
      title = this.$slots.default();
    } else if (this.refEl && !this.error) {
      title = [this.refEl.getAttribute('data-toc-title') || this.refEl.textContent];

      if (['H1', 'H2', 'H3', 'H4', 'H5', 'H6'].includes(this.refEl.tagName)) {
        const level = Number.parseInt(this.refEl.tagName.slice(1)) || 1;

        if (this.refEl.closest('.appendix')) {
          refClasses.push('ref-heading', 'ref-appendix');
          if (this.refEl.classList.contains('numbered')) {
            refClasses.push('ref-appendix-level' + level);
          }
        } else if (this.refEl.classList.contains('numbered')) {
          refClasses.push('ref-heading', 'ref-heading-level' + level);
        } else {
          refClasses.push('ref-heading');
        }
      } else if (this.refEl.tagName === 'FIGCAPTION') {
        refClasses.push('ref-figure');
      } else if (this.refEl.tagName === 'CAPTION') {
        refClasses.push('ref-table');
      }
    }

    return h('a', {href: '#' + this.refEl?.id || this.toId, class: refClasses}, [
      h('span', {class: 'ref-title'}, title)
    ]);
  },
  methods: {
    updateReference() {
      this.error = null;
      this.refEl = document.getElementById(this.toId);
      if (!this.refEl) {
        this.error = {
          message: 'Invalid reference',
          details: `Referenced element with id="${this.toId}" not found.`,
        };
        return;
      }

      // Check figure reference
      if (this.refEl.tagName === 'IMG') {
        this.refEl = this.refEl.closest('figure')?.querySelector('figcaption');
        if (!this.refEl) {
          this.error = {
            message: 'Invalid reference',
            details: `IMG element with id="${this.toId}" cannot be referenced, because it does not have a FIGCAPTION.`
          };
          return;
        }
      } else if (this.refEl.tagName === 'FIGURE') {
        this.refEl = this.refEl.querySelector('figcaption');
        if (!this.refEl) {
          this.error = {
            message: 'Invalid reference',
            details: `FIGURE element with id="${this.toId}" cannot be referenced, because it does not have a FIGCAPTION.`
          };
          return;
        }
      }
      if (this.refEl.tagName === 'FIGCAPTION' && !this.refEl.id) {
        this.refEl.setAttribute('id', uuidv4());
      }

      // Check table reference
      if (this.refEl.tagName === 'TABLE') {
        this.refEl = this.refEl.querySelector('caption');
        if (!this.refEl) {
          this.error = {
            message: 'Invalid reference',
            details: `TABLE element with id="${this.toId}" cannot be referenced, because it does not have a CAPTION.`
          };
          return;
        }
      }
      if (this.refEl.tagName === 'CAPTION' && !this.refEl.id) {
        this.refEl.setAttribute('id', uuidv4());
      }

      // Check heading reference
      const tagNames = ['H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'FIGCAPTION', 'CAPTION'];
      if (!tagNames.map(t => t.toUpperCase()).includes(this.refEl.tagName) && !this.$slots.default) {
        this.error = {
          message: 'Invalid reference',
          details: `${this.refEl.tagName} element with id="${this.toId}" cannot be automatically referenced. Provide a reference title manually (e.g. "[reference title](#${this.toId})" or "<ref to="${this.toId}">reference title</ref>").`
        };
        return;
      }

    }
  }
}
</script>

