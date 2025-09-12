<template>
  <list-view 
    url="/api/v1/pentestusers/"
    v-model:ordering="localSettings.userListOrdering"
    :ordering-options="[
      {id: 'created', title: 'Created', value: '-created'},
      {id: 'updated', title: 'Updated', value: '-updated'},
      {id: 'name', title: 'Name', value: 'username'},
    ]"
  >
    <template #title>Users</template>
    <template #actions>
      <btn-create 
        to="/users/new/" 
        :disabled="!auth.permissions.value.user_manager"
      />
    </template>
    <template #item="{item: user}: {item: User}">
      <v-list-item :to="`/users/${user.id}/`">
        <v-row>
          <v-col md="3">
            <v-list-item-title :data-testid="`user-${user.username}`">
              <user-avatar :user="user" class="mr-2" />
              {{ user.username }}
              <template v-if="user.name">
                ({{ user.name }})
              </template>
            </v-list-item-title>
          </v-col>
          <v-col md="3">
            <v-chip size="small" class="ma-1" v-if="user.is_superuser" text="Superuser" />
            <v-chip size="small" class="ma-1" v-if="user.is_project_admin" text="Project Admin" />
            <v-chip size="small" class="ma-1" v-if="user.is_user_manager" text="User Manager" />
            <v-chip size="small" class="ma-1" v-if="user.is_designer" text="Designer" />
            <v-chip size="small" class="ma-1" v-if="user.is_template_editor" text="Template Editor" />
            <v-chip size="small" class="ma-1" v-if="user.is_guest" text="Guest" />
            <v-chip size="small" class="ma-1" v-if="user.is_global_archiver" text="Global Archiver" />
            <v-chip size="small" class="ma-1" v-if="user.is_system_user" text="System" />
          </v-col>
          <v-col md="1">
            <v-chip size="small" class="ma-1" v-if="!user.is_system_user">
              <v-icon v-if="user.is_mfa_enabled" color="green" icon="mdi-check" />
              <v-icon v-else color="red" icon="mdi-close" />
              MFA
            </v-chip>
          </v-col>
          <v-col md="2">
            <v-chip size="small" class="ma-1" v-if="!user.is_system_user">Last Login: {{ (user.last_login || 'never').split('T')[0] }}</v-chip>
          </v-col>
          <v-col md="1">
            <v-chip size="small" class="ma-1" color="warning" v-if="!user.is_active">Inactive</v-chip>
          </v-col>
        </v-row>
      </v-list-item>
    </template>
  </list-view>
</template>

<script setup lang="ts">
definePageMeta({
  title: 'Users',
  toplevel: true,
});
useHeadExtended({
  breadcrumbs: () => userListBreadcrumbs(),
});

const auth = useAuth();
const localSettings = useLocalSettings();
</script>
