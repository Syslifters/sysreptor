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
      <v-card-title>Change Password</v-card-title>
      <v-card-text>
        <s-dialog v-model="changePasswordWizard.visible">
          <template #activator="{on, attrs}">
            <s-btn color="secondary" v-bind="attrs" v-on="on">
              Change Password
            </s-btn>
          </template>
          <template #title>Change Password</template>
          <template #default>
            <v-form ref="fromChangePassword">
              <v-card-text>
                <s-password-field 
                  v-model="changePasswordWizard.password" 
                  label="New Password"
                  :error-messages="changePasswordWizard.errors?.password" 
                  confirm show-strength
                />
              </v-card-text>
              <v-card-actions>
                <v-spacer />
                <s-btn @click="changePassword" :loading="actionInProgress" color="primary">
                  Change Password
                </s-btn>
              </v-card-actions>
            </v-form>
          </template>
        </s-dialog>
      </v-card-text>
    </s-card>

    <s-card class="mt-4">
      <v-card-title>Multi Factor Authentication</v-card-title>
      <v-card-text>
        <v-list>
          <v-list-item v-for="mfaMethod in mfaMethods" :key="mfaMethod.id">
            <v-list-item-title>
              <v-icon class="mr-3">{{ mfaMethodChoices.find(c => c.value === mfaMethod.method_type).icon }}</v-icon>
              {{ mfaMethod.name }}
              <template v-if="mfaMethod.is_primary">
                <v-chip small class="ml-3">Primary</v-chip>
              </template>
            </v-list-item-title>
            <v-list-item-action>
              <s-dialog v-model="editWizard.visible">
                <template #activator="{on, attrs}">
                  <s-btn @click="openEditWizard(mfaMethod)" icon v-bind="attrs" v-on="on">
                    <v-icon>mdi-pencil</v-icon>
                  </s-btn>
                </template>
                <template #title>Edit MFA</template>
                <template #default>
                  <v-card-text>
                    <p class="mb-6">
                      <v-icon class="mr-3">{{ editWizard.methodType.icon }}</v-icon>
                      {{ editWizard.methodType.text }}
                    </p>

                    <s-text-field 
                      v-model="editWizard.form.name"
                      label="Name"
                    />
                    <s-checkbox
                      v-model="editWizard.form.is_primary"
                      label="Primary MFA method"
                      hint="This MFA method is the default MFA method used for logins."
                    />
                  </v-card-text>
                  <v-card-actions>
                    <s-btn @click="editWizardSave" :loading="actionInProgress" color="primary">
                      Save
                    </s-btn>
                  </v-card-actions>
                </template>
              </s-dialog>
            </v-list-item-action>
            <v-list-item-action>
              <btn-delete icon :delete="() => deleteMfaMethod(mfaMethod)" />
            </v-list-item-action>
          </v-list-item>
          <v-list-item v-if="mfaMethods.length === 0">
            <v-list-item-title>Multi Factor Authentication is disabled</v-list-item-title>
          </v-list-item>

          <v-list-item>    
            <s-dialog v-model="setupWizard.visible">
              <template #activator="{on, attrs}">
                <s-btn color="secondary" @click="openSetupWizard" v-bind="attrs" v-on="on">
                  <v-icon>mdi-plus</v-icon>
                  Add
                </s-btn>
              </template>
              <template #title>Setup MFA</template>

              <template #default>
                <template v-if="setupWizard.step === 'choose_method_type'">
                  <v-card-text>
                    <s-select
                      v-model="setupWizard.methodType"
                      label="MFA Type"
                      :items="mfaMethodChoices"
                    >
                      <template #item="{item}">
                        <v-list-item-icon class="mr-3">
                          <v-icon>{{ item.icon }}</v-icon>
                        </v-list-item-icon>
                        <v-list-item-content>
                          <v-list-item-title>{{ item.text }}</v-list-item-title>
                        </v-list-item-content>
                      </template>
                      <template #selection="{item}">
                        <v-icon class="mr-3">{{ item.icon }}</v-icon> 
                        {{ item.text }}
                      </template>
                    </s-select>
                  </v-card-text>
                  <v-card-actions>
                    <v-spacer />
                    <s-btn 
                      @click="setupWizardRegisterBegin" 
                      :disabled="setupWizard.methodType === null"
                      :loading="actionInProgress" 
                      color="primary"
                    >
                      Next
                    </s-btn>
                  </v-card-actions>
                </template>

                <template v-else-if="setupWizard.step === 'complete_backup'">
                  <v-card-text>
                    <p>Please save following backup codes offline.</p>
                    <ul class="backup-code-list">
                      <li v-for="code in setupWizard.data.backup_codes" :key="code">{{ code }}</li>
                    </ul>
                  </v-card-text>

                  <v-card-actions>
                    <v-spacer />
                    <s-btn @click="setupWizardCompleteBackup" :loading="actionInProgress" color="primary">
                      Activate
                    </s-btn>
                  </v-card-actions>
                </template>

                <template v-else-if="setupWizard.step === 'complete_totp'">
                  <v-card-text>
                    <v-img :src="setupWizard.data.qrcode" contain max-width="40%" max-height="40%" />

                    <p>
                      Scan the QR code with your Authenticator App.<br />
                      If you cannot scan the QR code, here are the options to set up TOTP manually.
                      <ul>
                        <li>Secret key: <code>{{ setupWizard.data.s }}</code></li>
                        <li>Digits: {{ setupWizard.data.digits }}</li>
                        <li>Interval: {{ setupWizard.data.interval }}s</li>
                      </ul>
                    </p>

                    <p class="mb-0">Confirm TOTP Code:</p>
                    <v-otp-input
                      v-model="setupWizard.completeTotpForm.code"
                      type="number"
                      :length="setupWizard.data.digits"
                      :error-messages="setupWizard.error"
                      @finish="setupWizardCompleteTotp"
                      class="totp-confirm"
                    />
                  </v-card-text>
                  <v-card-actions>
                    <v-spacer />
                    <s-btn @click="setupWizardCompleteTotp" :loading="actionInProgress" color="primary">
                      Activate
                    </s-btn>
                  </v-card-actions>
                </template>

                <template v-else-if="setupWizard.step === 'complete_fido2'">
                  <v-card-text>
                    <p>
                      Confirm registration on your security key.
                    </p>

                    <v-alert v-if="setupWizard.error" color="error">
                      {{ setupWizard.error }} <s-btn @click="setupWizardRegisterBegin" text>Try again</s-btn>
                    </v-alert>
                  </v-card-text>
                </template>

                <template v-else-if="setupWizard.step === 'set_name'">
                  <v-card-text>
                    <p>
                      Set a name for the new MFA method to identify it later.
                    </p>

                    <s-text-field 
                      v-model="setupWizard.newMfaMethod.name" 
                      label="Name"
                    />
                  </v-card-text>
                  <v-card-actions>
                    <v-spacer />
                    <s-btn @click="setupWizardSetName" :loading="actionInProgress" color="primary">
                      Save
                    </s-btn>
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
import { create as navigatorCredentialsCreate, parseCreationOptionsFromJSON } from "@github/webauthn-json/browser-ponyfill";
import { cloneDeep } from 'lodash';
import { redirectToReAuth } from '~/utils/auth';
import { mfaMethodChoices } from '~/utils/other';

export default {
  async asyncData({ $axios, $auth, route }) {
    let mfaMethods = [];
    try {
      mfaMethods = await $axios.$get('/pentestusers/self/mfa/');
    } catch (error) {
      if (error?.response?.data?.code === 'reauth-required') {
        redirectToReAuth({ auth: $auth, route });
      } else {
        throw error;
      }
    }
    return { mfaMethods };
  },
  data() {
    return {
      setupWizard: {
        visible: false,
      },
      editWizard: {
        visible: false,
      },
      changePasswordWizard: {
        visible: false,
        password: '',
        errors: null,
      },
      actionInProgress: false,
      reauthDialogVisible: false,
    };
  },
  computed: {
    mfaMethodChoices() {
      return mfaMethodChoices;
    }
  },
  methods: {
    openSetupWizard() {
      this.setupWizard = {
        visible: true,
        step: 'choose_method_type',
        methodType: 'fido2',
        error: null,
        completeTotpForm: {
          code: null,
        },
        newMfaMethod: null,
      }
    },
    async requestWrapper(fn) {
      if (this.actionInProgress) {
        return false;
      }

      try {
        this.actionInProgress = true;
        await fn();
      } catch (error) {
        if (error?.response?.data?.code === 'reauth-required') {
          this.setupWizard.visible = false;
          this.reauthDialogVisible = true;
        }
        this.$toast.global.requestError({ error });
      } finally {
        this.actionInProgress = false;
      }
    },
    async setupWizardRegisterBegin() {
      await this.requestWrapper(async () => {
        this.setupWizard.data = await this.$axios.$post(`/pentestusers/self/mfa/register/${this.setupWizard.methodType}/begin/`, {});
        this.setupWizard.step = `complete_${this.setupWizard.methodType}`;
      });

      if (this.setupWizard.step === 'complete_fido2') {
        await this.setupWizardCompleteFido2();
      }
    },
    async setupCompleteWrapper(fn) {
      await this.requestWrapper(async () => {
        const obj = await fn();
        this.setupWizard.newMfaMethod = obj;
        this.setupWizard.step = 'set_name';
      });
    },
    async setupWizardCompleteBackup() {
      await this.setupCompleteWrapper(async () => {
        return await this.$axios.$post('/pentestusers/self/mfa/register/backup/complete/', {});
      });
    },
    async setupWizardCompleteTotp() {
      await this.setupCompleteWrapper(async () => {
        try {
          return await this.$axios.$post('/pentestusers/self/mfa/register/totp/complete/', this.setupWizard.completeTotpForm);
        } catch (error) {
          if (error?.response?.data?.detail) {
            this.setupWizard.error = error.response.data.detail;
          } else if (error?.response?.data?.non_field_errors) {
            this.setupWizard.error = error.response.data.non_field_errors[0];
          }
          throw error;
        }
      });
    },
    async setupWizardCompleteFido2() {
      await this.setupCompleteWrapper(async () => {
        try {
          const credential = await navigatorCredentialsCreate(parseCreationOptionsFromJSON(this.setupWizard.data.options));
          return await this.$axios.$post('/pentestusers/self/mfa/register/fido2/complete/', credential.toJSON());
        } catch (error) {
          if (error instanceof DOMException) {
            this.setupWizard.error = 'Security Key registration failed: ' + error.message;
          }
          throw error;
        }
      });
    },
    async setupWizardSetName() {
      await this.requestWrapper(async () => {
        const obj = await this.$axios.$patch(`/pentestusers/self/mfa/${this.setupWizard.newMfaMethod.id}/`, this.setupWizard.newMfaMethod);
        this.mfaMethods.push(obj);
        this.setupWizard.visible = false;
        this.$toast.success('MFA setup completed');
      });
    },
    openEditWizard(mfaMethod) {
      this.editWizard = {
        visible: true,
        methodType: this.mfaMethodChoices.find(c => c.value === mfaMethod.method_type),
        form: cloneDeep(mfaMethod),
      };
    },
    async editWizardSave() {
      await this.requestWrapper(async () => {
        await this.$axios.$patch(`/pentestusers/self/mfa/${this.editWizard.form.id}/`, this.editWizard.form);
        this.mfaMethods = await this.$axios.$get('/pentestusers/self/mfa/');
        this.editWizard.visible = false;
      });
    },
    async deleteMfaMethod(mfaMethod) {
      await this.requestWrapper(async () => {
        await this.$axios.$delete(`/pentestusers/self/mfa/${mfaMethod.id}/`);
        this.mfaMethods = this.mfaMethods.filter(m => m.id !== mfaMethod.id);
      });
    },
    async changePassword() {
      if (!this.$refs.fromChangePassword.validate()) {
        return;
      }

      await this.requestWrapper(async () => {
        try {
          this.changePasswordWizard.errors = null;
          await this.$axios.$post('/pentestusers/self/change-password/', {
            password: this.changePasswordWizard.password,
          });
          this.changePasswordWizard.visible = false;
          this.changePasswordWizard.password = '';
          this.$toast.success('Password changed');
        } catch (error) {
          if (error?.response?.status === 400 && error?.response?.data?.password) {
            this.changePasswordWizard.errors = error?.response.data;
          }
        }
      });
    },
    redirectToReAuth() {
      redirectToReAuth({ auth: this.$auth, route: this.$route });
    }
  }
}
</script>

<style lang="scss" scoped>
.backup-code-list {
  list-style: none;
  columns: 2;
  color: black;
}

.totp-confirm {
  max-width: 30em;
}
</style>
