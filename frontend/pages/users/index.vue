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
          </v-col>
          <v-col md="2">
            <v-chip small class="ma-1">Last Login: {{ (user.last_login || 'never').split('T')[0] }}</v-chip>
          </v-col>
          <v-col md="1">
            <v-chip small class="ma-1" color="warning" v-if="!user.is_active">Inactive</v-chip>
          </v-col>
        </v-row>
      </v-list-item>
    </template>
  </list-view>
</template>
