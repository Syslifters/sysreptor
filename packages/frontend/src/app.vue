<template>
  <v-app :theme="theme">
    <nuxt-layout>
      <nuxt-page />
    </nuxt-layout>
  </v-app>
</template>

<script setup lang="ts">
const route = useRoute();
const auth = useAuth();
const localSettings = useLocalSettings();
const apiSettings = useApiSettings();

useHeadExtended({
  titleTemplate: title => rootTitleTemplate(title, route),
});

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
watch(theme, () => {
  document.documentElement.style.setProperty('color-scheme', (theme.value.toLowerCase().includes('dark') ? 'dark' : 'light'));
}, { immediate: true });


const router = useRouter();
watch(router.currentRoute, () => {
  // Reset browser-based spellcheck on navigation
  if (!apiSettings.settings?.features.spellcheck) {
    localSettings.setAllSpellcheckSettings(false);
  }
})
</script>
