<template>
  <v-app :theme="theme">
    <nuxt-layout>
      <nuxt-page />
    </nuxt-layout>
  </v-app>
</template>

<script setup lang="ts">
const route = useRoute();
useHeadExtended({
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

<!-- TODO: [x] font: Noto Sans instead of Exo 2 -->
<!-- TODO: [x] container without fluid for settings pages and lists -->
<!-- TODO: [x] list views: tabs below list instead of filters -->
<!-- TODO: [x] remove s-sub-menu -->
<!-- TODO: [x] use <full-height-page> in <list-view> -->
<!-- TODO: [x] refactor project list -->
<!-- TODO: [x] refactor design list -->
<!-- TODO: [ ] how to handle scope selection in designs? -->
<!-- TODO: [ ] main drawer: isActive based on route path start instead of default -->
