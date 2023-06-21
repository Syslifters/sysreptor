<template>
  <v-form ref="form">
    <edit-toolbar 
      :data="user" 
      :form="$refs.form" 
      :edit-mode="canEdit ? 'EDIT' : 'READONLY'" 
      :save="performSave"
      :delete="performDelete"
      :delete-confirm-input="user.username"
    />

    <user-info-form v-model="user" :errors="serverErrors" :can-edit-permissions="canEdit" :can-edit-username="canEdit">
      <template #login-information>
        <s-btn v-if="canEdit" :to="`/users/${user.id}/reset-password/`" nuxt color="secondary">
          Reset Password
        </s-btn>

        <s-checkbox 
          v-model="user.is_active" 
          :disabled="!canEdit"
          label="User is active" 
          hint="Inactive users cannot log in"
        />
        <s-checkbox 
          v-model="user.can_login_local"
          label="Local user"
          hint="The user can log in with username and password."
          disabled
        />
        <s-checkbox
          v-if="ssoEnabled"
          v-model="user.can_login_sso"
          label="SSO user"
          hint="The user can login with an authentication provider. It has linked identities configured."
          disabled
        />
      </template>
      <s-checkbox
        v-if="localUserAuthEnabled && !user.is_system_user"
        v-model="user.is_mfa_enabled"
        label="Is Multi Factor Authentication enabled"
        disabled
      />
      <p v-if="!user.is_system_user" class="mt-4">
        Last login: {{ user.last_login || 'Never' }}
      </p>
    </user-info-form>
  </v-form>
</template>
    </user-info-form>
  </v-form>
</template>

<script>
function getUserUrl(params) {
  return `/pentestusers/${params.userId}/`;
}

export default {
  async asyncData({ params, $axios }) {
    return {
      user: await $axios.$get(getUserUrl(params)),
    };
  },
  data() {
    return {
      serverErrors: null,
    }
  },
  computed: {
    canEdit() {
      return this.$auth.hasScope('user_manager') && !this.user.is_system_user;
    },
    ssoEnabled() {
      return this.$store.getters['apisettings/settings'].auth_providers.some(p => ['oidc', 'remoteuser'].includes(p.type));
    },
    localUserAuthEnabled() {
      return this.$store.getters['apisettings/settings'].auth_providers.some(p => p.type === 'local');
    }
  },
  methods: {
    async performSave(data) {
      try {
        await this.$axios.$patch(getUserUrl({ userId: data.id }), data);
        this.serverErrors = null;
      } catch (error) {
        if (error?.response?.status === 400 && error?.response?.data) {
          this.serverErrors = error.response.data;
        }
        throw error;
      }
    },
    async performDelete(data) {
      await this.$axios.$delete(getUserUrl({ userId: data.id }));
      this.$toast.success('User deleted');
      this.$router.push('/users/');
    }
  }
}
</script>
