<template>
  <v-autocomplete 
    v-bind="$attrs" 
    v-on="$listeners" 
    hide-no-data
    hide-details="auto" 
    :outlined="outlined"
    class="mt-4"
  >
    <template v-for="_, name in $scopedSlots" :slot="name" slot-scope="data"><slot :name="name" v-bind="data" /></template>
    <template v-for="_, name in $slots" :slot="name"><slot :name="name" /></template>
  </v-autocomplete>
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
