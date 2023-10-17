<template>
  <v-tabs class="sub-menu" hide-slider height="30" selected-class="text-primary">
    <slot />
  </v-tabs>
</template>

<style lang="scss" scoped>
.sub-menu :deep(.v-tab) {
  text-transform: initial;
}
</style>
