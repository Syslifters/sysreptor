<template>
  <v-container>
    <v-form ref="form">
      <edit-toolbar :form="$refs.form" :save="performCreate">
        <template #title>Create new User</template>
        <template #save-button-text>Create User</template>
      </edit-toolbar>

      <user-info-form v-model="user" :errors="serverErrors" :can-edit-permissions="true" :can-edit-username="true">
        <template #login-information>
          <s-password-field 
            v-model="user.password" 
            confirm show-strength
            :error-messages="serverErrors?.password"
          />
        </template>
      </user-info-form>
    </v-form>
  </v-container>
</template>

<script>
export default {
  data() {
    return {
      user: {
        username: null,
        password: null,
        title_before: null,
        first_name: null,
        middle_name: null,
        last_name: null,
        title_after: null,
        email: null,
        phone: null,
        mobile: null,
        is_superuser: !this.$store.getters['apisettings/is_professional_license'],
        is_user_manager: false,
        is_designer: false,
        is_template_editor: false,
        is_guest: false,
        is_system_user: false,
      },
      serverErrors: null,
    }
  },
  methods: {
    async performCreate() {
      if (!this.$refs.form.validate()) {
        return;
      }

      try {
        const user = await this.$axios.$post('/pentestusers/', this.user);
        this.$router.push({ path: `/users/${user.id}/` });
      } catch (error) {
        if (error?.response?.status === 400 && error?.response?.data) {
          this.serverErrors = error.response.data;
        }
        this.$toast.global.requestError({ error });
      }
    }
  }
}
</script>
