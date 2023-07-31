<template>
  <v-list-item-title class="d-flex">
    <chip-cvss :risk-score="translation.risk_score" /> 
    <div class="pt-2 pb-2 flex-grow-1 wrap-content">
      {{ translation.data.title }}
      <br />
      <chip-review-status v-if="translation.status !== 'finished'" :value="translation.status" />
      <s-tooltip v-for="tr in value.translations" :key="tr.id">
        <template #activator="{attrs, on}">
          <chip-language :value="tr.language" v-bind="attrs" v-on="on" />
        </template>
        <template #default>
          {{ tr.data.title }}
        </template>
      </s-tooltip>
      <chip-tag v-for="tag in value.tags" :key="tag" :value="tag" />
    </div>
    <v-spacer />
    <s-tooltip>
      <template #activator="{on}">
        <s-btn :to="{path: `/templates/${value.id}/`, query: {language}}" target="_blank" nuxt icon class="ma-2" v-on="on">
          <v-icon>mdi-chevron-right-circle</v-icon>
        </s-btn>
      </template>
      <template #default>Show template</template>
    </s-tooltip>
  </v-list-item-title>
</template>

<script>
export default {
  props: {
    value: {
      type: Object,
      required: true,
    },
    language: {
      type: String,
      default: null,
    },

  },
  computed: {
    translation() {
      return this.value.translations.find(tr => tr.language === this.language) || this.value.translations.find(tr => tr.is_main);
    }
  }
}
</script>

<style lang="scss" scoped>
.wrap-content {
  white-space: normal;
}
</style>
