<template>
  <v-container>
    <v-form ref="form">
      <edit-toolbar :data="user" :form="$refs.form" :edit-mode="canEdit ? 'EDIT' : 'READONLY'" :save="performSave" />

      <user-info-form v-model="user" :errors="serverErrors" :can-edit-permissions="true" :can-edit-username="true">
        <template #login-information>
          <s-btn v-if="canEdit" :to="`/users/${user.id}/reset-password/`" nuxt color="secondary">
            Reset Password
          </s-btn>

          <s-checkbox 
            v-model="user.is_active" 
            label="User is active" 
            hint="Inactive users cannot log in"
          />
          <p class="mt-4">
            Last login: {{ user.last_login || 'Never' }}
          </p>
        </template>
      </user-info-form>
    </v-form>
  </v-container>
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
      return this.$auth.hasScope('user_manager') || this.user.id === this.$auth.user.id;
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
    }
  }
}
</script>
