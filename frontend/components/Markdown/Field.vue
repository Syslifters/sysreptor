<script>
import VTextArea from 'vuetify/lib/components/VTextarea/VTextarea';
import mixins from 'vuetify/lib/util/mixins';
import MarkdownFieldNewVue from './Editor.vue';

const baseMixins = mixins(VTextArea);
export default baseMixins.extend({
  extends: VTextArea,

  props: {
    outlined: {
      type: Boolean,
      default: true,
    },
    lang: {
      type: String,
      default: null,
    },
    uploadImage: {
      type: Function,
      default: null,
    },
    imageUrlsRelativeTo: {
      type: String,
      default: null,
    },
  },
  computed: {
    isLabelActive() {
      return true;
    }
  },
  methods: {
    genInput() {
      return this.$createElement(MarkdownFieldNewVue, {
        props: {
          value: this.value,
          disabled: this.disabled,
          lang: this.lang,
          uploadImage: this.uploadImage,
          imageUrlsRelativeTo: this.imageUrlsRelativeTo,
          
        },
        attrs: {
          class: 'markdown-editor'
        },
        on: {
          input: (value) => {
            this.$emit('input', value);
          }
        }
      })
    }
  },
})
</script>

<style lang="scss" scoped>
.v-input__slot {
  padding: 0 1px !important;
}
.v-text-field__slot {
  margin-right: 0 !important;
  max-width: 100%;

  label {
    // Value of private variable: $text-field-enclosed-details-padding - 1px
    left: 11px !important;
  }
}
.markdown-editor {
  width: 100%;
}
</style>
