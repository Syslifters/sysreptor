<template>
  <v-select 
    hide-details="auto" 
    :error-count="100"
    :outlined="outlined" 
    persistent-hint
    class="mt-1"
    v-bind="$attrs" 
    v-on="$listeners"
  >
    <template v-for="_, name in $scopedSlots" :slot="name" slot-scope="data"><slot :name="name" v-bind="data" /></template>
    <template v-for="_, name in $slots" :slot="name"><slot :name="name" /></template>
  </v-select>
</template>

<script>
export default {
  props: {
    outlined: {
      type: Boolean,
      default: true,
    }
  },
}
</script>
