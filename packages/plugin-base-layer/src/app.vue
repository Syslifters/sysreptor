<template>
  <v-app :theme="isDarkTheme ? 'dark' : 'light'">
    <nuxt-layout>
      <nuxt-page />
    </nuxt-layout>
  </v-app>
</template>

<script setup lang="ts">

// Inherit parent theme configs
const theme = useTheme();
onBeforeMount(() => {
  try {
    const parentThemeConfig = window.parent?.useNuxtApp?.().$vuetify?.theme;
    if (parentThemeConfig) {
      for (const themeName of Object.keys(theme.themes.value)) {
        if (parentThemeConfig.themes.value[themeName]) {
          theme.themes.value[themeName] = parentThemeConfig.themes.value[themeName];
        }
      }
      theme.themes.value = parentThemeConfig.themes.value;
    }
  } catch {
    // ignore error
  }
});


// Set theme
const colorSchemeQueryList = window.matchMedia('(prefers-color-scheme: dark)');
const isDarkTheme = ref<boolean>(colorSchemeQueryList.matches);
colorSchemeQueryList.addEventListener('change', (event) => {
  isDarkTheme.value = event.matches;
});
</script>
