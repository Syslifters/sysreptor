<template>
  <v-list-item v-bind="$attrs" v-on="$listeners">
    <v-list-item-content>
      <v-list-item-title>
        <chip-cvss :risk-score="translation.risk_score" />
        {{ translation.data.title }}
      </v-list-item-title>
      <v-list-item-subtitle>
        <chip-review-status :value="translation.status" />
        <s-tooltip v-for="tr in value.translations" :key="tr.id">
          <template #activator="{attrs, on}">
            <chip-language :value="tr.language" v-bind="attrs" v-on="on" />
          </template>
          <template #default>
            {{ tr.data.title }}
          </template>
        </s-tooltip>
        <chip-tag v-for="tag in value.tags" :key="tag" :value="tag" />
      </v-list-item-subtitle>
    </v-list-item-content>
  </v-list-item>
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
      return this.value.translations.find(tr => tr.language === this.language) || this.value.translations.find(t => t.is_main);
    },
  },
}
</script>
