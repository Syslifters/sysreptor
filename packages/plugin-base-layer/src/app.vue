<template>
  <v-app :theme="isDarkTheme ? 'dark' : 'light'">
    <nuxt-layout>
      <nuxt-page />
    </nuxt-layout>
  </v-app>
</template>

<script setup lang="ts">
const colorSchemeQueryList = window.matchMedia('(prefers-color-scheme: dark)');
const isDarkTheme = ref<boolean>(colorSchemeQueryList.matches);
colorSchemeQueryList.addEventListener('change', (event) => {
  isDarkTheme.value = event.matches;
});
</script>
