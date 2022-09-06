<template>
  <s-select 
    :value="value" @change="$emit('input', $event)" 
    :disabled="disabled"
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
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      languageInfos: [],
    }
  },
  async fetch() {
    this.languageInfos = await this.$store.dispatch('apisettings/getLanguages');
  },
}
</script>
