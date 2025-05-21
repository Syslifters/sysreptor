<template>
  <s-btn-icon>
    <v-icon icon="mdi-account" />

    <v-menu activator="parent" location="bottom" data-testid="profile-menu-modal">
      <v-list>
        <v-list-item
          v-if="auth.user.value"
          lines="two"
          :title="auth.user.value.username"
          :subtitle="auth.user.value.name || ''"
        >
          <template #prepend>
            <user-avatar :user="auth.user.value" />
          </template>
        </v-list-item>
        <v-list-item
          v-else
          title="Logged out"
        />
        <v-divider />
        <v-list-item
          v-if="auth.loggedIn.value"  
          to="/users/self/"
          prepend-icon="mdi-account"
          title="Profile"
          data-testid="profile-button"
        />
        <template v-if="auth.loggedIn.value && apiSettings.isProfessionalLicense">
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
          v-if="auth.loggedIn.value"
          @click="auth.logout"
          prepend-icon="mdi-logout"
          title="Log out"
          link
        />
        <v-list-item
          v-else
          to="/login/"
          prepend-icon="mdi-login"
          title="Log in"
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
