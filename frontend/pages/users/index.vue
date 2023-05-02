<template>
  <list-view url="/pentestusers/">
    <template #title>Users</template>
    <template #actions v-if="$auth.hasScope('user_manager')">
      <s-btn color="primary" to="/users/new/" nuxt>
        <v-icon>mdi-plus</v-icon>
        Create
      </s-btn>
    </template>
    <template #item="{item: user}">
      <v-list-item :to="`/users/${user.id}/`" nuxt>
        <v-row>
          <v-col md="3">
            <v-list-item-title>
              {{ user.username }}
              <template v-if="user.name">
                ({{ user.name }})
              </template>
            </v-list-item-title>
          </v-col>
          <v-col md="3">
            <v-chip small class="ma-1" v-if="user.is_superuser">Superuser</v-chip>
            <v-chip small class="ma-1" v-if="user.is_user_manager">User Manager</v-chip>
            <v-chip small class="ma-1" v-if="user.is_designer">Designer</v-chip>
            <v-chip small class="ma-1" v-if="user.is_template_editor">Template Editor</v-chip>
            <v-chip small class="ma-1" v-if="user.is_guest">Guest</v-chip>
            <v-chip small class="ma-1" v-if="user.is_global_archiver">Global Archiver</v-chip>
            <v-chip small class="ma-1" v-if="user.is_system_user">System</v-chip>
          </v-col>
          <v-col md="1">
            <v-chip small class="ma-1" v-if="!user.is_system_user">
              <v-icon v-if="user.is_mfa_enabled" color="green">mdi-check</v-icon>
              <v-icon v-else color="red">mdi-close</v-icon>
              MFA
            </v-chip>
          </v-col>
          <v-col md="2">
            <v-chip small class="ma-1" v-if="!user.is_system_user">Last Login: {{ (user.last_login || 'never').split('T')[0] }}</v-chip>
          </v-col>
          <v-col md="1">
            <v-chip small class="ma-1" color="warning" v-if="!user.is_active">Inactive</v-chip>
          </v-col>
        </v-row>
      </v-list-item>
    </template>
  </list-view>
</template>

<script>
export default {
  head: {
    title: 'Users',
  },
}
</script>
