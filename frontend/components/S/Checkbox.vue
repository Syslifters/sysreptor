<template>
  <v-checkbox :input-value="value" @change="$emit('input', $event)" v-bind="$attrs" v-on="$listeners" persistent-hint hide-details="auto">
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
