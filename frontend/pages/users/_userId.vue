<template>
  <split-menu :value="15">
    <template #menu>
      <v-list dense>
        <v-list-item-title class="text-h6 pl-2">{{ user.username }}</v-list-item-title>
        <v-list-item :to="`/users/${user.id}/`" exact nuxt>
          <v-list-item-icon>
            <v-icon>mdi-account</v-icon>
          </v-list-item-icon>
          <v-list-item-title>User Information</v-list-item-title>
        </v-list-item>
        <v-list-item :to="`/users/${user.id}/reset-password/`" nuxt>
          <v-list-item-icon>
            <v-icon>mdi-form-textbox-password</v-icon>
          </v-list-item-icon>
          <v-list-item-title>Reset Password</v-list-item-title>
        </v-list-item>
        <v-list-item :to="`/users/${user.id}/mfa/`" nuxt>
          <v-list-item-icon>
            <v-icon>mdi-lock</v-icon>
          </v-list-item-icon>
          <v-list-item-title>Multi Factor Authentication</v-list-item-title>
        </v-list-item>
        <v-list-item v-if="oidcEnabled" :to="`/users/${user.id}/identities/`" nuxt>
          <v-list-item-icon>
            <v-icon>mdi-card-account-details</v-icon>
          </v-list-item-icon>
          <v-list-item-title>Identities</v-list-item-title>
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
  async asyncData({ $axios, params }) {
    return {
      user: await $axios.$get(`/pentestusers/${params.userId}/`),
    };
  },
  computed: {
    oidcEnabled() {
      return this.$store.getters['apisettings/settings'].auth_providers.length > 0;
    }
  }
}
</script>
