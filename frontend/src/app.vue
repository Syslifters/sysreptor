<template>
  <v-app :theme="theme">
    <nuxt-layout>
      <nuxt-page />
    </nuxt-layout>
  </v-app>
</template>

<script setup lang="ts">
const route = useRoute();
useHead({
  titleTemplate: title => rootTitleTemplate(title, route),
});

const auth = useAuth();
const localSettings = useLocalSettings();
const apiSettings = useApiSettings();

const colorSchemeQueryList = window.matchMedia('(prefers-color-scheme: dark)');
const systemThemeIsDark = ref<boolean>(colorSchemeQueryList.matches);
colorSchemeQueryList.addEventListener('change', (event) => {
  systemThemeIsDark.value = event.matches;
});

const theme = computed(() => {
  let baseTheme = localSettings.theme;
  if (!baseTheme || !['light', 'dark'].includes(baseTheme)) {
    // Use system theme
    if (systemThemeIsDark.value) {
      baseTheme = 'dark';
    } else {
      baseTheme = 'light';
    }
  }

  // Admin theme
  if (apiSettings.isProfessionalLicense && auth.user.value?.scope.includes('admin')) {
    return baseTheme + 'Admin';
  } else {
    return baseTheme;
  }
});
</script>
