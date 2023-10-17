<template>
  <span class="loader-spinner">
    <v-icon icon="mdi-cached" />
  </span>
</template>

<style scoped lang="scss">
  .loader-spinner {
    animation: loader 1s infinite;
    display: inline-flex;
  }
  @keyframes loader {
    from {
      transform: rotate(0);
    }
    to {
      transform: rotate(-360deg);
    }
  }
</style>
