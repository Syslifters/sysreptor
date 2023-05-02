<template>
  <s-tooltip v-if="value">
    <template #activator="{on, attrs}">
      <v-list-item-icon v-on="on" v-bind="attrs" class="lock-info-icon">
        <v-icon x-small>mdi-pencil-lock</v-icon>
      </v-list-item-icon>
    </template>

    <span>{{ value.user.username }} is editing</span>
  </s-tooltip>
</template>

<script>
export default {
  props: {
    value: {
      type: [Object, null],
      default: null,
    }
  }
}
</script>

<style lang="scss" scoped>
.lock-info-icon {
  margin-right: 0 !important;
  min-width: 1em !important;
}
</style>
