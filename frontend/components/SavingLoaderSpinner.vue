<template>
  <span class="loader-spinner">
    <v-icon>mdi-cached</v-icon>
  </span>
</template>

<style scoped>
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
