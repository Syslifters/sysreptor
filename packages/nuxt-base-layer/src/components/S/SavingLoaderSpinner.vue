<template>
  <span>
    <v-icon icon="mdi-sync" class="animation-rotate" />
  </span>
</template>

<style scoped lang="scss">
  .animation-rotate {
    animation: rotate 1s infinite;
  }
  @keyframes rotate {
    from {
      transform: rotate(0);
    }
    to {
      transform: rotate(-360deg);
    }
  }
</style>
