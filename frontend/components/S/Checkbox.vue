<template>
  <v-checkbox 
    :input-value="value" 
    @change="$emit('input', $event)" 
    persistent-hint 
    hide-details="auto"
    :error-count="100"
    v-bind="$attrs" 
    v-on="$listeners"
  >
    <template v-for="_, name in $scopedSlots" :slot="name"><slot :name="name" /></template>
  </v-checkbox>
</template>

<script>
export default {
  props: {
    value: {
      type: Boolean,
      required: true,
    },
  }
}
</script>
