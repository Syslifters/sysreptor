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

<!-- TODO: permissions: disable instead of hiding 
* [x] Archived Projects in menu
* [x] Archive button in Project menu
* [x] Public key page in user menu
* [x] SSO Identities in user menu
* [x] create design
* [x] import design
* [x] create template
* [x] import template
* [x] create user
* [x] guest permissions
  * [x] apiSettings: provide guest permission settings to frontend
  * [x] create project
  * [x] import project
  * [x] change project settings
  * [x] delete project
  * [x] customize design in project
  * [x] finish project
  * [x] archive project
  * [x] copy project
* [x] EditToolbar
  * [x] archive button
  * [x] context actions
  * [x] save button
  * [x] delete button
* [x] version history: temporary hover over sub-drawer
* [ ] add "/PRO" badge when in community edition for disabled features
  * [x] buttons and menus
  * [ ] sudo button in main drawer ???
  * [ ] sudo in user menu ???
-->
