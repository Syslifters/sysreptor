<template>
  <v-tabs v-bind="$attrs" v-on="$listeners" class="sub-menu" hide-slider>
    <slot />
  </v-tabs>
</template>

<style lang="scss" scoped>
.sub-menu :deep(.v-tabs-bar) {
  height: 30px;

  .v-tab {
    text-transform: initial;
  }
}
</style>
