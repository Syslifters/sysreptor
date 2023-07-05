<template>
  <div>
    <s-dialog v-model="reauthDialogVisible">
      <template #title>Re-Authentication required</template>
      <template #default>
        <v-card-text>
          This operation requires a re-authentication.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <s-btn @click="reauthDialogVisible = false" color="secondary">
            Cancel
          </s-btn>
          <s-btn @click="redirectToReAuth" color="primary">Re-Authenticate</s-btn>
        </v-card-actions>
      </template>
    </s-dialog>

    <s-card class="mt-4">
      <v-card-title>API Tokens</v-card-title>
      <v-card-text>
        <v-list>
          <v-list-item v-for="apiToken in apiTokens" :key="apiToken.id">
            <v-list-item-icon>
              <v-icon>mdi-key-variant</v-icon>
            </v-list-item-icon>
            <v-list-item-title>
              {{ apiToken.name }}
              <chip-expires class="ml-3" :value="apiToken.expire_date" />
            </v-list-item-title>
            <v-list-item-action>
              <btn-delete icon :delete="() => deleteApiToken(apiToken)" />
            </v-list-item-action>
          </v-list-item>
          <v-list-item>
            <s-dialog v-model="setupWizard.visible">
              <template #activator="{ on, attrs}">
                <s-btn color="secondary" @click="openSetupWizard" v-bind="attrs" v-on="on">
                  <v-icon>mdi-plus</v-icon>
                  Add
                </s-btn>
              </template>
              <template #title>Setup API Token</template>
              <template #default>
                <template v-if="setupWizard.step === 'info'">
                  <v-card-text>
                    <s-text-field
                      v-model="setupWizard.form.name"
                      label="Name"
                      :error-messages="setupWizard.errors?.name"
                      class="mb-4"
                      autofocus
                    />
                    <s-date-picker
                      v-model="setupWizard.form.expire_date"
                      label="Expire Date (optional)"
                      :error-messages="setupWizard.errors?.expire_date"
                    />
                  </v-card-text>
                  <v-card-actions>
                    <v-spacer />
                    <s-btn @click="setupWizard.visible = false" color="secondary">
                      Cancel
                    </s-btn>
                    <s-btn @click="createApiToken" color="primary" :loading="setupWizard.actionInProgress">
                      Create
                    </s-btn>
                  </v-card-actions>
                </template>
                <template v-else-if="setupWizard.step === 'token'">
                  <v-card-text>
                    <p>
                      The API token <code>{{ setupWizard.newApiToken.name }}</code> has been created successfully.<br>
                      Please copy the token and store it in a safe place.
                      You will not be able to see it again.
                    </p>
                    <pre class="token-preview"><code>Authorization: Bearer {{ setupWizard.newApiToken.token }}</code></pre>
                  </v-card-text>
                  <v-card-actions>
                    <v-spacer />
                    <s-btn @click="setupWizard.visible = false" color="primary">Done</s-btn>
                  </v-card-actions>
                </template>
              </template>
            </s-dialog>
          </v-list-item>
        </v-list>
      </v-card-text>
    </s-card>
  </div>
</template>

<script>
import { redirectToReAuth } from '~/utils/auth';

export default {
  async asyncData({ $axios, $auth, route }) {
    let apiTokens = [];
    try {
      apiTokens = await $axios.$get('/pentestusers/self/apitokens/');
    } catch (error) {
      if (error?.response?.data?.code === 'reauth-required') {
        redirectToReAuth({ auth: $auth, route });
      } else {
        throw error;
      }
    }
    return { apiTokens };
  },
  data() {
    return {
      reauthDialogVisible: false,
      setupWizard: {
        visible: false,
        step: 'info',
        form: {
          name: '',
          expire_date: null,
        },
        errors: null,
        actionInProgress: false,
        newApiToken: null,
      }
    }
  },
  methods: {
    openSetupWizard() {
      this.setupWizard = {
        visible: false,
        step: 'info',
        form: {
          name: 'API Token',
          expire_date: null,
        },
        errors: null,
        actionInProgress: false,
        newApiToken: null,
      };
    },
    async createApiToken() {
      try {
        this.setupWizard.newApiToken = await this.$axios.$post('/pentestusers/self/apitokens/', this.setupWizard.form);
        this.setupWizard.step = 'token';
        this.apiTokens.push(this.setupWizard.newApiToken);
      } catch (error) {
        if (error?.response?.data?.code === 'reauth-required') {
          this.setupWizard.visible = false;
          this.reauthDialogVisible = true;
        } else if (error?.response?.data) {
          this.setupWizard.errors = error.response.data;
        } else {
          throw error;
        }
      }
    },
    async deleteApiToken(apiToken) {
      try {
        await this.$axios.$delete(`/pentestusers/self/apitokens/${apiToken.id}/`);
        this.apiTokens = this.apiTokens.filter(t => t.id !== apiToken.id);
      } catch (error) {
        this.$toast.global.requestError({ error });
      }
    },
    redirectToReAuth() {
      redirectToReAuth({ auth: this.$auth, route: this.$route });
    },
  }
}
</script>

<style lang="scss" scoped>
.token-preview {
  white-space: pre-wrap;
  word-break: break-all;

  code {
    display: block;
  }
}
</style>
