<template>
  <v-list-item to="/license/" title="License">
    <template #prepend>
      <v-badge :color="licenseError ? 'error' : licenseWarning ? 'warning' : 'transparent'" dot>
        <v-icon icon="mdi-check-decagram" />
      </v-badge>
    </template>
  </v-list-item>
</template>

<script setup lang="ts">
const apiSettings = useApiSettings();

useLazyAsyncData(async () => {
  if (apiSettings.isProfessionalLicense) {
    await apiSettings.getLicenseInfo();
  }
});

const licenseError = computed(() => apiSettings.settings!.license.error !== null);
const licenseWarning = computed(() => {
  if (!apiSettings.licenseInfo || !apiSettings.licenseInfo.valid_until) {
    return false;
  }
  const warnThresholdDate = new Date();
  warnThresholdDate.setDate(new Date().getDate() + 2 * 30);
  return new Date(apiSettings.licenseInfo.valid_until) < warnThresholdDate;
});
</script>
