<template>
  <full-height-page>
    <list-view url="/api/v1/pentestusers/">
      <template #title>Users</template>
      <template #actions v-if="auth.hasScope('user_manager')">
        <btn-create to="/users/new/" />
      </template>
      <template #item="{item: user}: {item: User}">
        <v-list-item :to="`/users/${user.id}/`">
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
              <v-chip size="small" class="ma-1" v-if="user.is_superuser" text="Superuser" />
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
  </full-height-page>
</template>

<script setup lang="ts">
definePageMeta({
  title: 'Users',
  toplevel: true,
});
useHead({
  breadcrumbs: () => userListBreadcrumbs(),
});

const auth = useAuth();
</script>
