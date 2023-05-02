<template>
  <v-tooltip 
    v-bind="$attrs" 
    v-on="$listeners" 
    transition="fade-transition" 
    max-width="50%" 
    :open-delay="openDelay" 
    top
  >
    <template v-for="_, name in $scopedSlots" :slot="name" slot-scope="data"><slot :name="name" v-bind="data" /></template>
  </v-tooltip>
</template>

<script>
export default {
  props: {
    openDelay: {
      type: Number,
      default: 200,
    }
  },
}
</script>
