<template>
  <s-autocomplete 
    v-bind="$attrs"
    :value="value" @change="$emit('input', $event)" 
    :items="languageInfos"
    item-value="code"
    :item-text="l => l.name + (l.code ? ' (' + l.code + ')' : '')"
    label="Language"
  >
    <template #prepend-inner>
      <v-icon small left>mdi-translate</v-icon>
    </template>
    <template #item="{item}">
      <v-icon small left>mdi-translate</v-icon>
      {{ item.name }}<template v-if="item.code"> ({{ item.code }})</template>
    </template>
  </s-autocomplete>
</template>

<script>
export default {
  props: {
    value: {
      type: String,
      default: null,
    },
    items: {
      type: Array,
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
      return this.items || this.$store.getters['apisettings/settings'].languages.filter(l => l.enabled || l.code === this.initialLanguage);
    }
  }
}
</script>
