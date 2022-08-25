import { h } from "vue";

export default {
  props: {
    comma: {
      type: String,
      default: ', ',
    },
    and: {
      type: String,
      default: ' and ',
    }
  },

  render() {
    const slots = Object.values(this.$slots).map(s => s());
    let children = [];
    for (let i = 0; i < slots.length; i++) {
      children.push(slots[i]);
      if (i < slots.length - 2) {
        children.push(this.comma);
      } else if (i === slots.length - 2) {
        children.push(this.and);
      }
    }

    return h('span', children);
  }
}
