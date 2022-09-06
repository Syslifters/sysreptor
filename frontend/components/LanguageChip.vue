<template>
  <v-chip class="ma-1" small>
    Language: {{ languageInfo.name }}
  </v-chip>
</template>

<script>
export default {
  props: {
    value: {
      type: String,
      required: true,
    }
  },
  data() {
    return {
      languageInfos: [],
    }
  },
  async fetch() {
    this.languageInfos = await this.$store.dispatch('apisettings/getLanguages');
  },
  computed: {
    languageInfo() {
      return this.languageInfos.find(l => l.code === this.value) || { code: '??-??', name: 'Unknown' };
    }
  }
}
</script>
