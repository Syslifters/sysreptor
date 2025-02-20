<template>
  <v-container class="h-100 overflow-y-auto">
    <h1>License Info</h1>

    <p v-if="license.error" class="text-error mt-2">
      <v-icon start color="error" icon="mdi-alert-decagram" />
      License Error: {{ license.error }}<br>
      Falling back to a free community license. Some features are disabled.<br>
      See <a href="https://docs.sysreptor.com/features-and-pricing/" target="_blank" class="text-primary">https://docs.sysreptor.com/features-and-pricing/</a>
    </p>

    <v-table class="table-key-value">
      <tbody>
        <tr>
          <td>License Type:</td>
          <td>{{ license.type }}</td>
        </tr>
        <tr v-if="license.name">
          <td>Licensed to:</td>
          <td>{{ license.name }}</td>
        </tr>
        <tr v-if="license.valid_from">
          <td>Valid from:</td>
          <td>{{ license.valid_from }}</td>
        </tr>
        <tr v-if="license.valid_until">
          <td>Valid until:</td>
          <td>
            {{ license.valid_until }}
            <v-chip v-if="new Date(license.valid_until) < new Date()" text="Expired" color="error" size="small" class="ml-2" />
            <v-chip v-else-if="licenseWarning" text="Expires soon" color="warning" size="small" class="ml-2" />
          </td>
        </tr>
        <tr>
          <td>Max. Users:</td>
          <td>{{ license.users }}</td>
        </tr>
        <tr>
          <td>Active Users:</td>
          <td>
            {{ license.active_users }}
            <v-chip v-if="license.active_users > license.users" text="Limit exceeded" color="error" size="small" class="ml-2" />
          </td>
        </tr>
        <tr>
          <td>Software Version:</td>
          <td>{{ license.software_version }}</td>
        </tr>
        <tr>
          <td>Plugins:</td>
          <td>{{ license.plugins.join(', ') || '-' }}</td>
        </tr>
      </tbody>
    </v-table>
  </v-container>
</template>

<script setup lang="ts">
definePageMeta({
  title: 'License',
  toplevel: true,
});
useHeadExtended({
  breadcrumbs: () => [{ title: 'License', to: '/license/' }],
});

const license = await useFetchE<LicenseInfoDetails>('/api/v1/utils/license/', { method: 'GET' });
const licenseWarning = computed(() => {
  if (!license.value || !license.value.valid_until) {
    return false;
  }
  const warnThresholdDate = new Date();
  warnThresholdDate.setDate(new Date().getDate() + 2 * 30);
  return new Date(license.value.valid_until) < warnThresholdDate;
});
</script>

<style lang="scss" scoped>
.table-key-value {
  td:first-child {
    font-weight: bold;
    width: 15em;
  }

  td:last-child {
    width: auto;
  }
}
</style>
