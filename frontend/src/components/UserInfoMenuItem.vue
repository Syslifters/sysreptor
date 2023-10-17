<template>
  <v-btn icon>
    <v-badge :color="licenseError ? 'error' : licenseWarning ? 'warning' : 'transparent'" dot>
      <v-icon color="white" icon="mdi-account" />
    </v-badge>

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
            v-if="auth.hasScope('admin')"
            :to="{path: '/users/self/admin/disable/', query: { next: route.fullPath }}"
            prepend-icon="mdi-account-arrow-down"
            title="Disable Superuser Permissions"
          />
          <v-list-item
            v-else-if="auth.user.value!.is_superuser"
            :to="{path: '/users/self/admin/enable/', query: { next: route.fullPath }}"
            prepend-icon="mdi-account-arrow-up"
            title="Enable Superuser Permissions"
          />
        </template>
        <v-list-item
          v-if="showLicense"
          to="/license/"
          title="License Info"
        >
          <template #prepend>
            <v-badge :color="licenseError ? 'error' : licenseWarning ? 'warning' : 'transparent'" dot>
              <v-icon icon="mdi-check-decagram" />
            </v-badge>
          </template>
        </v-list-item>
        <v-list-item
          @click="auth.logout"
          prepend-icon="mdi-logout"
          title="Log out"
          link
        />
      </v-list>
    </v-menu>
  </v-btn>
</template>

<script setup lang="ts">
const auth = useAuth();
const apiSettings = useApiSettings();
const route = useRoute();

const showLicense = computed(() => auth.hasScope('user_manager') || auth.user.value!.is_superuser);
const licenseError = computed(() => apiSettings.settings!.license.error !== null);
const { data: licenseInfo } = useLazyAsyncData(async () => {
  if (showLicense.value && licenseError.value) {
    return await $fetch<LicenseInfoDetails>('/api/v1/utils/license/', { method: 'GET' });
  } else {
    return null;
  }
});
const licenseWarning = computed(() => {
  if (!licenseInfo.value || !licenseInfo.value.valid_until) {
    return false;
  }
  const warnThresholdDate = new Date();
  warnThresholdDate.setDate(new Date().getDate() + 2 * 30);
  return new Date(licenseInfo.value.valid_until) < warnThresholdDate;
});
</script>
