<template>
  <v-menu left bottom offset-y>
    <template #activator="{ on, attrs }">
      <v-btn v-bind="attrs" v-on="on" icon dark>
        <v-badge v-if="licenseError" dot color="error"><v-icon>mdi-account</v-icon></v-badge>
        <v-badge v-else-if="licenseWarning" dot color="warning"><v-icon>mdi-account</v-icon></v-badge>
        <v-icon v-else>mdi-account</v-icon>
      </v-btn>
    </template>

    <template #default>
      <v-list>
        <v-list-item two-line>
          <v-list-item-content>
            <v-list-item-title>{{ $auth.user.username }}</v-list-item-title>
            <v-list-item-subtitle>{{ $auth.user.name }}</v-list-item-subtitle>
          </v-list-item-content>
        </v-list-item>
        <v-divider />
        <v-list-item to="/users/self/" nuxt>
          <v-list-item-icon><v-icon>mdi-account</v-icon></v-list-item-icon>
          <v-list-item-title>Profile</v-list-item-title>
        </v-list-item>
        <template v-if="$store.getters['apisettings/is_professional_license']">
          <v-list-item v-if="$auth.hasScope('admin')" to="/users/self/admin/disable/" nuxt>
            <v-list-item-icon><v-icon>mdi-account-arrow-down</v-icon></v-list-item-icon>
            <v-list-item-title>Disable Superuser Permissions</v-list-item-title>
          </v-list-item>
          <v-list-item v-else-if="$auth.user.is_superuser" to="/users/self/admin/enable/" nuxt>
            <v-list-item-icon><v-icon>mdi-account-arrow-up</v-icon></v-list-item-icon>
            <v-list-item-title>Enable Superuser Permissions</v-list-item-title>
          </v-list-item>
        </template>
        <v-list-item v-if="showLicense" to="/license">
          <v-list-item-icon>
            <v-badge v-if="licenseError" dot color="error"><v-icon>mdi-alert-decagram</v-icon></v-badge>
            <v-badge v-else-if="licenseWarning" dot color="warning"><v-icon>mdi-check-decagram</v-icon></v-badge>
            <v-icon v-else>mdi-check-decagram</v-icon>
          </v-list-item-icon>
          <v-list-item-title>License Info</v-list-item-title>
        </v-list-item>
        <v-list-item link @click="logout()">
          <v-list-item-icon><v-icon>mdi-logout</v-icon></v-list-item-icon>
          <v-list-item-title>Log out</v-list-item-title>
        </v-list-item>
      </v-list>
    </template>
  </v-menu>
</template>

<script>
export default {
  data() {
    return {
      licenseInfo: null,
    };
  },
  async fetch() {
    if (this.showLicense && !this.licenseError) {
      this.licenseInfo = await this.$axios.$get('/utils/license');
    }
  },
  computed: {
    showLicense() {
      return this.$auth.hasScope('user_manager') || this.$auth.user.is_superuser;
    },
    licenseError() {
      return this.$store.getters['apisettings/settings'].license.error !== null;
    },
    licenseWarning() {
      return this.licenseInfo && new Date(this.licenseInfo.valid_until) < new Date().setDate(new Date().getDate() + 2 * 30);
    },
  },
  methods: {
    async logout() {
      await this.$auth.logout();
    },
  },
};
</script>
