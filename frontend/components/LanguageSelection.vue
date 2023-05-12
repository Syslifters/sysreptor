<template>
  <s-autocomplete 
    v-bind="$attrs"
    :value="value" @change="$emit('input', $event)" 
    :items="languageInfos"
    item-value="code"
    :item-text="l => l.name + ' (' + l.code + ')'"
    label="Language"
    class="mt-4"
  />
</template>

<script>
export default {
  props: {
    value: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      initialLanguage: this.value,
    };
  },
  computed: {
    languageInfos() {
      return this.$store.getters['apisettings/settings'].languages.filter(l => l.enabled || l.code === this.initialLanguage);
    }
  }
}
</script>
