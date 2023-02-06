<template>
  <s-select 
    v-bind="$attrs"
    :value="value" @change="$emit('input', $event)" 
    :items="languageInfos"
    item-value="code"
    item-text="name"
    label="Language"
    class="mt-4"
  />
</template>

<script>
export default {
  props: {
    value: {
      type: String,
      required: true,
    },
  },
  computed: {
    languageInfos() {
      return this.$store.getters['apisettings/settings'].languages;
    }
  }
}
</script>
