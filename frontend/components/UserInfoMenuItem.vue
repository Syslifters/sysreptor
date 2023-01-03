<template>
  <v-menu left bottom offset-y>
    <template #activator="{ on, attrs }">
      <v-btn v-bind="attrs" v-on="on" icon dark>
        <v-icon>mdi-account</v-icon>
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
          <v-list-item-title>Profile</v-list-item-title>
        </v-list-item>
        <v-list-item link @click="logout()">
          <v-list-item-title>Log out</v-list-item-title>
        </v-list-item>
      </v-list>
    </template>
  </v-menu>
</template>

<script>
export default {
  methods: {
    async logout() {
      await this.$auth.logout();
    },
  },
};
</script>
