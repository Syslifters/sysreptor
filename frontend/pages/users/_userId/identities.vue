<template>
  <s-card>
    <v-card-title>SSO Identities</v-card-title>
    <v-card-text>
      <v-data-table
        :headers="[{text: 'SSO Provider', value: 'provider'}, {text: 'Identifier', value: 'identifier'}, {text: 'Actions', value: 'actions'}]"
        :items="identities"
        disable-sort disable-pagination disable-filtering hide-default-footer
      >
        <template #item.provider="{item}">
          {{ ssoAuthProviders.find(p => p.id === item.provider)?.name || item.provider }}
        </template>
        <template #item.actions="{item}">
          <btn-delete :delete="() => deleteIdentity(item)" icon :disabled="!canEdit" />
        </template>
      </v-data-table>

      <s-dialog v-model="createWizard.visible">
        <template #activator="{on, attrs}">
          <s-btn v-bind="attrs" v-on="on" :disabled="!canEdit" color="secondary">
            <v-icon>mdi-plus</v-icon>Add
          </s-btn>
        </template>
        <template #title>Add Identity</template>
        <template #default>
          <v-card-text>
            <s-select
              v-model="createWizard.form.provider"
              label="SSO Provider"
              :items="ssoAuthProviders"
              item-value="id"
              item-text="name"
              :error-messages="createWizard.errors?.provider"
            />
            <s-text-field
              v-model="createWizard.form.identifier"
              label="Identifier"
              :error-messages="createWizard.errors?.identifier"
              class="mt-4"
            />
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <s-btn @click="createIdentity" :loading="createWizard.actionInProgress" color="primary">
              Save
            </s-btn>
          </v-card-actions>
        </template>
      </s-dialog>
    </v-card-text>
  </s-card>
</template>

<script>
export default {
  async asyncData({ $axios, params }) {
    const [user, identities] = await Promise.all([
      $axios.$get(`pentestusers/${params.userId}/`),
      $axios.$get(`/pentestusers/${params.userId}/identities/`)
    ])
    return { user, identities };
  },
  data() {
    return {
      createWizard: {
        visible: false,
        actionInProgress: false,
        errors: null,
        form: {
          provider: null,
          identifier: null,
        }
      }
    }
  },
  computed: {
    canEdit() {
      return this.$auth.hasScope('user_manager') && !this.user.is_system_user;
    },
    ssoAuthProviders() {
      return this.$store.getters['apisettings/settings'].auth_providers.filter(p => ['oidc', 'remoteuser'].includes(p.type));
    }
  },
  methods: {
    async createIdentity() {
      try {
        this.createWizard.actionInProgress = true;

        const obj = await this.$axios.$post(`/pentestusers/${this.user.id}/identities/`, this.createWizard.form);
        this.identities.push(obj);
        this.createWizard.visible = false;
      } catch (error) {
        if (error?.request?.data) {
          this.createWizard.errors = error.request.data;
        }
        this.$toast.global.requestError({ error });
      } finally {
        this.createWizard.actionInProgress = false;
      }
    },
    async deleteIdentity(identity) {
      await this.$axios.$delete(`/pentestusers/${this.user.id}/identities/${identity.id}/`);
      this.identities = this.identities.filter(i => i.id !== identity.id);
    },
  }
}
</script>
