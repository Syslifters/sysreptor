<template>
  <s-btn-icon>
    <v-icon icon="mdi-account" />

    <v-menu activator="parent" location="bottom">
      <v-list>
        <v-list-item
          lines="two"
          :title="auth.user.value!.username"
          :subtitle="auth.user.value!.name || ''"
        />
        <v-divider />
        <v-list-item
          to="/users/self/"
          prepend-icon="mdi-account"
          title="Profile"
        />
        <template v-if="apiSettings.isProfessionalLicense">
          <v-list-item
            v-if="auth.permissions.value.admin"
            :to="{path: '/users/self/admin/disable/', query: { next: route.fullPath }}"
            prepend-icon="mdi-account-arrow-down"
            title="Disable Superuser Permissions"
          />
          <v-list-item
            v-else-if="auth.permissions.value.superuser"
            :to="{path: '/users/self/admin/enable/', query: { next: route.fullPath }}"
            prepend-icon="mdi-account-arrow-up"
            title="Enable Superuser Permissions"
          />
        </template>
        <v-list-item
          @click.stop="localSettings.theme = localSettings.theme === 'light' ? 'dark' : localSettings.theme === 'dark' ? null : 'light'"
          :prepend-icon="localSettings.theme === 'dark' ? 'mdi-weather-night' : localSettings.theme === 'light' ? 'mdi-weather-sunny' : 'mdi-theme-light-dark'"
          :title="localSettings.theme === 'dark' ? 'Theme: Dark' : localSettings.theme === 'light' ? 'Theme: Light' : 'Theme: System'"
        />
        <v-list-item
          @click="auth.logout"
          prepend-icon="mdi-logout"
          title="Log out"
          link
        />
      </v-list>
    </v-menu>
  </s-btn-icon>
</template>

<script setup lang="ts">
const route = useRoute();
const auth = useAuth();
const localSettings = useLocalSettings();
const apiSettings = useApiSettings();
</script>
