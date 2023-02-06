<template>
  <v-chip class="ma-1" small>
    {{ languageInfo.name }}
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
  computed: {
    languageInfo() {
      return this.$store.getters['apisettings/settings'].languages.find(l => l.code === this.value) || { code: '??-??', name: 'Unknown' };
    }
  }
}
</script>
