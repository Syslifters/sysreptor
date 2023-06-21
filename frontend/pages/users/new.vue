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
            v-if="localUserAuthEnabled" 
            v-model="user.password" 
            confirm show-strength
            :error-messages="serverErrors?.password"
          />
          <div v-if="ssoAuthProviders.length > 0">
            SSO Authentication Identity (optional):
            <v-row>
              <v-col>
                <s-select
                  v-model="identity.provider"
                  label="Provider"
                  :items="ssoAuthProviders"
                  item-value="id"
                  item-text="name"
                />
              </v-col>
              <v-col>
                <s-text-field
                  v-model="identity.identifier"
                  label="Identifier"
                  class="mt-1"
                />
              </v-col>
            </v-row>
          </div>
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
        first_name: '',
        middle_name: null,
        last_name: '',
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
        is_global_archiver: false,
      },
      identity: {
        provider: null,
        identifier: null,
      },
      serverErrors: null,
    }
  },
  computed: {
    authProviders() {
      return this.$store.getters['apisettings/settings'].auth_providers;
    },
    localUserAuthEnabled() {
      return this.authProviders.some(p => p.type === 'local');
    },
    ssoAuthProviders() {
      return this.authProviders.filter(p => ['oidc', 'remoteuser'].includes(p.type));
    },
  },
  methods: {
    async performCreate() {
      if (!this.$refs.form.validate()) {
        return;
      }

      try {
        const user = await this.$axios.$post('/pentestusers/', this.user);

        if (this.identity.provider && this.identity.identifier) {
          try {
            await this.$axios.$post(`/pentestusers/${user.id}/identities/`, this.identity);
          } catch (error) {
            this.$toast.global.requestError({ error });
          }
        }
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
