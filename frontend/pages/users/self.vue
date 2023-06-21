<template>
  <split-menu :value="15">
    <template #menu>
      <v-list dense>
        <v-list-item-title class="text-h6 pl-2">User Profile</v-list-item-title>
        <v-list-item to="/users/self/" exact nuxt>
          <v-list-item-icon>
            <v-icon>mdi-account</v-icon>
          </v-list-item-icon>
          <v-list-item-title>User Information</v-list-item-title>
        </v-list-item>
        <v-list-item v-if="localUserAuthEnabled" to="/users/self/security/" nuxt>
          <v-list-item-icon>
            <v-icon>mdi-lock</v-icon>
          </v-list-item-icon>
          <v-list-item-title>Security</v-list-item-title>
        </v-list-item>
        <v-list-item v-if="archivingEnabled" to="/users/self/publickeys/" nuxt>
          <v-list-item-icon>
            <v-icon>mdi-folder-key</v-icon>
          </v-list-item-icon>
          <v-list-item-title>Archiving Public Keys</v-list-item-title>
        </v-list-item>
      </v-list>
    </template>
    
    <template #default>
      <nuxt-child />
    </template>
  </split-menu>
</template>

<script>
export default {
  head() {
    return {
      titleTemplate: title => this.$root.$options.head.titleTemplate((title ? `${title} | ` : '') + 'Profile'),
    }
  },
  computed: {
    archivingEnabled() {
      return this.$store.getters['apisettings/settings'].features.archiving;
    },
    localUserAuthEnabled() {
      return this.$store.getters['apisettings/settings'].auth_providers.some(p => p.type === 'local');
    }
  },
}
</script>
