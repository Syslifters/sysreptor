<template>
  <v-menu left bottom offset-y>
    <template #activator="{ on, attrs }">
      <v-btn v-bind="attrs" v-on="on" icon dark>
        <v-icon>mdi-account</v-icon>
      </v-btn>
    </template>

    <template #default>
      <v-list>
        <v-list-item>
          <v-list-item-content>
            <v-list-item-title>
              {{ $auth.user.name }}
            </v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-divider />
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
      await this.$auth.logout({
        data: {
          refresh: this.$auth.strategy.refreshToken,
        }
      });
    },
  },
};
</script>
