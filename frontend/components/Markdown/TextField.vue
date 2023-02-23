<script>
import VTextField from 'vuetify/lib/components/VTextField/VTextField';
import mixins from 'vuetify/lib/util/mixins';
import MarkdownTextFieldContent from './TextFieldContent.vue';

const baseMixins = mixins(VTextField);
export default baseMixins.extend({
  extends: VTextField,

  props: {
    outlined: {
      type: Boolean,
      default: true,
    },
    persistentHint: {
      type: Boolean,
      default: true,
    },
    hideDetails: {
      type: [String, Array],
      default: "auto",
    },
    errorCount: {
      type: Number,
      default: 100,
    },

    lang: {
      type: String,
      default: null,
    },
    spellcheckSupported: {
      type: Boolean,
      default: false,
    },
  },
  methods: {
    genInput() {
      return this.$createElement(MarkdownTextFieldContent, {
        props: {
          value: this.value,
          disabled: this.disabled,
          lang: this.lang,
          spellcheckSupported: this.spellcheckSupported,
        },
        on: {
          input: (value) => {
            this.$emit('input', value);
          },
          blur: this.onBlur,
          focus: (e) => {
            if (!this.isFocused) {
              this.isFocused = true;
              this.$emit('focus', e);
            }
          },
        }
      });
    },
  },
})
</script>

<style lang="scss" scoped>
.v-input__slot, .v-text-field__slot {
  width: 100%;
  max-width: 100%;
}
</style>
