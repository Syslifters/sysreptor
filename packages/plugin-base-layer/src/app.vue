<template>
  <v-app>
    <nuxt-layout>
      <nuxt-page />
    </nuxt-layout>
  </v-app>
</template>

<script setup lang="ts">
import { merge } from 'lodash-es';

// Inherit parent theme configs
const theme = useTheme();
onBeforeMount(() => {
  try {
    const parentThemeConfig = window.parent?.useNuxtApp?.().$vuetify?.theme;
    if (parentThemeConfig) {
      const themes = {} as any;
      for (const themeName of ['light', 'dark']) {
        if (parentThemeConfig.themes.value[themeName]) {
          themes[themeName] = merge({}, theme.themes.value[themeName], parentThemeConfig.themes.value[themeName]);
        }
      }
      theme.themes.value = themes;
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
watch(isDarkTheme, () => theme.change(isDarkTheme.value ? 'dark' : 'light'), { immediate: true });
</script>
