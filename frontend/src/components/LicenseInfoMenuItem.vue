<template>
  <v-list-item to="/license/" title="License" :disabled="!showLicense">
    <template #prepend>
      <v-badge :color="licenseError ? 'error' : licenseWarning ? 'warning' : 'transparent'" dot>
        <v-icon icon="mdi-check-decagram" />
      </v-badge>
    </template>
  </v-list-item>
</template>

<script setup lang="ts">
const auth = useAuth();
const apiSettings = useApiSettings();

const showLicense = computed(() => auth.hasScope('user_manager') || auth.user.value!.is_superuser);
const licenseError = computed(() => apiSettings.settings!.license.error !== null);
const { data: licenseInfo } = useLazyAsyncData(async () => {
  if (showLicense.value && licenseError.value) {
    await nextTick();
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
