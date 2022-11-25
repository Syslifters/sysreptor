<template>
  <v-combobox
    v-bind="$attrs" 
    v-on="$listeners" 
    hide-details="auto"
    :error-count="100"
    persistent-hint
    :outlined="outlined"
    class="mt-4"
    spellcheck="false"
  >
    <template v-for="_, name in $scopedSlots" :slot="name" slot-scope="data"><slot :name="name" v-bind="data" /></template>
    <template v-for="_, name in $slots" :slot="name"><slot :name="name" /></template>
  </v-combobox>
</template>

<script>
export default {
  props: {
    outlined: {
      type: Boolean,
      default: true,
    }
  }
}
</script>
