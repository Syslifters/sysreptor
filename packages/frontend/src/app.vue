<template>
  <v-app>
    <nuxt-layout>
      <nuxt-page />
    </nuxt-layout>
    <toast-snackbar-queue />
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
useEventListener(colorSchemeQueryList, 'change', (event: MediaQueryListEvent) => {
  systemThemeIsDark.value = event.matches;
});

const vuetifyTheme = useTheme();
const themeName = computed(() => {
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
watch(themeName, () => {
  document.documentElement.style.setProperty('color-scheme', (themeName.value.toLowerCase().includes('dark') ? 'dark' : 'light'));
  vuetifyTheme.change(themeName.value);
}, { immediate: true });


const router = useRouter();
watch(router.currentRoute, () => {
  // Reset browser-based spellcheck on navigation
  if (auth.loggedIn.value && apiSettings.settings && !apiSettings.settings.features.spellcheck) {
    localSettings.setAllSpellcheckSettings(false);
  }
})
</script>
