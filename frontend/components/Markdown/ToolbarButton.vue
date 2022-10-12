<template>
  <s-tooltip>
    <template #activator="{on, attrs}">
      <s-btn :disabled="disabled" @click="$emit('click', $event)" v-bind="attrs" v-on="on" icon small tile :outlined="active">
        <v-icon small>{{ icon }}</v-icon>
      </s-btn>
    </template>
    <template #default><span>{{ title }}</span></template>
  </s-tooltip>
</template>

<script>
export default {
  props: {
    icon: {
      type: String,
      required: true,
    },
    title: {
      type: String,
      default: '',
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    active: {
      type: Boolean,
      default: false,
    },
  },
}
</script>

<style lang="scss" scoped>
.v-btn--outlined {
  border-radius: 15%;
}
</style>
