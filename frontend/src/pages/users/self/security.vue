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
          <s-btn-other
            @click="reauthDialogVisible = false"
            text="Cancel"
          />
          <s-btn-primary
            @click="auth.redirectToReAuth({ replace: true })"
            text="Re-Authenticate"
          />
        </v-card-actions>
      </template>
    </s-dialog>

    <s-card class="mt-4">
      <v-card-title>Change Password</v-card-title>
      <v-card-text>
        <s-dialog v-model="changePasswordWizard.visible">
          <template #activator="{ props: dialogProps }">
            <s-btn-secondary
              text="Change Password"
              v-bind="dialogProps"
            />
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
                <s-btn-primary
                  @click="changePassword"
                  :loading="actionInProgress"
                  text="Change Password"
                />
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
          <v-list-item
            v-for="mfaMethod in mfaMethods" :key="mfaMethod.id"
            :icon="mfaMethodChoices.find(c => c.value === mfaMethod.method_type)?.icon"
          >
            <v-list-item-title>
              {{ mfaMethod.name }}
              <template v-if="mfaMethod.is_primary">
                <v-chip size="small" class="ml-3" text="Primary" />
              </template>
            </v-list-item-title>
            <template #append>
              <s-dialog v-model="editWizard.visible">
                <template #activator="{props: dialogProps}">
                  <s-btn-icon
                    @click="openEditWizard(mfaMethod)"
                    icon="mdi-pencil"
                    v-bind="dialogProps"
                  />
                </template>
                <template #title>Edit MFA</template>
                <template #default>
                  <v-card-text>
                    <p class="mb-6">
                      <v-icon start :icon="editWizard.methodType.icon" />
                      {{ editWizard.methodType.text }}
                    </p>

                    <s-text-field
                      v-model="editWizard.form!.name"
                      label="Name"
                      class="mt-4"
                      spellcheck="false"
                    />
                    <s-checkbox
                      v-model="editWizard.form!.is_primary"
                      label="Primary MFA method"
                      hint="This MFA method is the default MFA method used for logins."
                      class="mt-4"
                    />
                  </v-card-text>
                  <v-card-actions>
                    <v-spacer />
                    <s-btn-primary
                      @click="editWizardSave"
                      :loading="actionInProgress"
                      text="Save"
                    />
                  </v-card-actions>
                </template>
              </s-dialog>

              <btn-delete
                button-variant="icon"
                :delete="() => deleteMfaMethod(mfaMethod)"
              />
            </template>
          </v-list-item>
          <v-list-item
            v-if="mfaMethods.length === 0"
            title="Multi Factor Authentication is disabled"
          />

          <v-list-item>
            <s-dialog v-model="setupWizard.visible">
              <template #activator="{ props: dialogProps }">
                <s-btn-secondary
                  @click="openSetupWizard"
                  v-bind="dialogProps"
                  prepend-icon="mdi-plus"
                  text="Add"
                />
              </template>
              <template #title>Setup MFA</template>

              <template #default>
                <template v-if="setupWizard.step === SetupWizardStep.ChooseMethodType">
                  <v-card-text>
                    <s-select
                      v-model="setupWizard.methodType"
                      label="MFA Type"
                      :items="mfaMethodChoices"
                      class="mt-1"
                    >
                      <template #item="{props: {title: item, ...itemProps}}">
                        <v-list-item v-bind="itemProps" :prepend-icon="(item as any).icon" :title="(item as any).text" />
                      </template>
                      <template #selection="{item: {props: {title: item}}}">
                        <v-icon :icon="(item as any).icon" start />
                        {{ (item as any).text }}
                      </template>
                    </s-select>
                  </v-card-text>
                  <v-card-actions>
                    <v-spacer />
                    <s-btn-primary
                      @click="setupWizardRegisterBegin"
                      :disabled="!setupWizard.methodType"
                      :loading="actionInProgress"
                      text="Next"
                    />
                  </v-card-actions>
                </template>

                <template v-else-if="setupWizard.step === SetupWizardStep.CompleteBackup">
                  <v-card-text>
                    <p>Please save following backup codes offline.</p>
                    <ul class="backup-code-list">
                      <li v-for="code in setupWizard.data.backup_codes" :key="code">{{ code }}</li>
                    </ul>
                  </v-card-text>

                  <v-card-actions>
                    <v-spacer />
                    <s-btn-primary
                      @click="setupWizardCompleteBackup"
                      :loading="actionInProgress"
                      text="Activate"
                    />
                  </v-card-actions>
                </template>

                <template v-else-if="setupWizard.step === SetupWizardStep.CompleteTotp">
                  <v-card-text>
                    <v-img :src="setupWizard.data.qrcode" alt="qrcode" max-width="40%" max-height="40%" />

                    <p>
                      Scan the QR code with your Authenticator App.<br />
                      If you cannot scan the QR code, here are the options to set up TOTP manually.
                    </p>
                    <ul class="ml-8 mb-4">
                      <li>Secret key: <s-code>{{ setupWizard.data.s }}</s-code></li>
                      <li>Digits: {{ setupWizard.data.digits }}</li>
                      <li>Interval: {{ setupWizard.data.interval }}s</li>
                    </ul>

                    <p class="mb-0">Confirm TOTP Code:</p>
                    <v-otp-input
                      v-model="setupWizard.completeTotpForm.code"
                      type="number"
                      :length="setupWizard.data.digits"
                      @finish="setupWizardCompleteTotp"
                      :error-messages="setupWizard.error"
                      class="totp-confirm"
                    />
                  </v-card-text>
                  <v-card-actions>
                    <v-spacer />
                    <s-btn-primary
                      @click="setupWizardCompleteTotp"
                      :loading="actionInProgress"
                      text="Activate"
                    />
                  </v-card-actions>
                </template>

                <template v-else-if="setupWizard.step === SetupWizardStep.CompleteFido2">
                  <v-card-text>
                    <p>
                      Confirm registration on your security key.
                    </p>

                    <v-alert v-if="setupWizard.error" type="error">
                      {{ setupWizard.error }}
                      <s-btn-other
                        @click="setupWizardRegisterBegin"
                        text="Try again"
                      />
                    </v-alert>
                  </v-card-text>
                </template>

                <template v-else-if="setupWizard.step === SetupWizardStep.SetName">
                  <v-card-text>
                    <p>
                      Set a name for the new MFA method to identify it later.
                    </p>

                    <s-text-field
                      v-model="setupWizard.newMfaMethod!.name"
                      label="Name"
                      class="mt-4"
                      spellcheck="false"
                    />
                  </v-card-text>
                  <v-card-actions>
                    <v-spacer />
                    <s-btn-primary
                      @click="setupWizardSetName"
                      :loading="actionInProgress"
                      text="Save"
                    />
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

<script setup lang="ts">
import { create as navigatorCredentialsCreate, parseCreationOptionsFromJSON } from "@github/webauthn-json/browser-ponyfill";
import { cloneDeep } from 'lodash-es';
import type { VForm } from "vuetify/lib/components/index.mjs";
import { mfaMethodChoices, MfaMethodType } from '@/utils/types';

const auth = useAuth();

const mfaMethods = await useAsyncDataE(async () => {
  try {
    return await $fetch<MfaMethod[]>('/api/v1/pentestusers/self/mfa/', { method: 'GET' });
  } catch (error: any) {
    if (error?.data?.code === 'reauth-required') {
      auth.redirectToReAuth({ replace: true });
      return [];
    } else {
      throw error;
    }
  }
});

const reauthDialogVisible = ref(false);

enum SetupWizardStep {
  ChooseMethodType = 'choose_method_type',
  CompleteBackup = 'complete_backup',
  CompleteTotp = 'complete_totp',
  CompleteFido2 = 'complete_fido2',
  SetName = 'set_name',
}
const setupWizard = ref<{
  visible: boolean,
  step: SetupWizardStep,
  methodType: MfaMethodType,
  data: any | null,
  error?: string,
  completeTotpForm: {
    code: string,
  },
  newMfaMethod: MfaMethod | null,
}>({
  visible: false,
  step: SetupWizardStep.ChooseMethodType,
  methodType: MfaMethodType.FIDO2,
  data: null,
  error: undefined,
  completeTotpForm: {
    code: '',
  },
  newMfaMethod: null,
});

const editWizard = ref<{
  visible: boolean,
  methodType: any | null,
  form: MfaMethod | null,
}>({
  visible: false,
  methodType: null,
  form: null,
});

const changePasswordWizard = ref<{
  visible: boolean,
  password: string,
  errors: string[] | null | any,
}>({
  visible: false,
  password: '',
  errors: null,
});

const actionInProgress = ref(false);
async function requestWrapper(fn: () => Promise<void>) {
  if (actionInProgress.value) {
    return false;
  }

  try {
    actionInProgress.value = true;
    await fn();
  } catch (error: any) {
    if (error?.data?.code === 'reauth-required') {
      setupWizard.value.visible = false;
      editWizard.value.visible = false;
      reauthDialogVisible.value = true;
    } else {
      requestErrorToast({ error });
    }
  } finally {
    actionInProgress.value = false;
  }
}

function openSetupWizard() {
  setupWizard.value = {
    visible: true,
    step: SetupWizardStep.ChooseMethodType,
    methodType: MfaMethodType.FIDO2,
    data: null,
    error: undefined,
    completeTotpForm: {
      code: '',
    },
    newMfaMethod: null,
  }
}
async function setupWizardRegisterBegin() {
  await requestWrapper(async () => {
    setupWizard.value.data = await $fetch(`/api/v1/pentestusers/self/mfa/register/${setupWizard.value.methodType}/begin/`, {
      method: 'POST',
      body: {},
    });
    setupWizard.value.step = {
      [MfaMethodType.FIDO2]: SetupWizardStep.CompleteFido2,
      [MfaMethodType.TOTP]: SetupWizardStep.CompleteTotp,
      [MfaMethodType.BACKUP]: SetupWizardStep.CompleteBackup,
    }[setupWizard.value.methodType];
  });

  if (setupWizard.value.step === SetupWizardStep.CompleteFido2) {
    await setupWizardCompleteFido2();
  }
}

async function setupCompleteWrapper(fn: () => Promise<MfaMethod>) {
  await requestWrapper(async () => {
    const obj = await fn();
    setupWizard.value.newMfaMethod = obj;
    setupWizard.value.step = SetupWizardStep.SetName;
  });
}
async function setupWizardCompleteFido2() {
  await setupCompleteWrapper(async () => {
    try {
      const credential = await navigatorCredentialsCreate(parseCreationOptionsFromJSON(setupWizard.value.data.options));
      return await $fetch<MfaMethod>('/api/v1/pentestusers/self/mfa/register/fido2/complete/', {
        method: 'POST',
        body: credential.toJSON(),
      });
    } catch (error: any) {
      if (error instanceof DOMException) {
        setupWizard.value.error = 'Security Key registration failed: ' + error.message;
      }
      throw error;
    }
  });
}
async function setupWizardCompleteBackup() {
  await setupCompleteWrapper(async () => {
    return await $fetch<MfaMethod>('/api/v1/pentestusers/self/mfa/register/backup/complete/', {
      method: 'POST',
      body: {},
    });
  });
}
async function setupWizardCompleteTotp() {
  await setupCompleteWrapper(async () => {
    try {
      return await $fetch<MfaMethod>('/api/v1/pentestusers/self/mfa/register/totp/complete/', {
        method: 'POST',
        body: setupWizard.value.completeTotpForm,
      });
    } catch (error: any) {
      if (error?.data?.detail) {
        setupWizard.value.error = error.data.detail;
      } else if (error?.data?.non_field_errors) {
        setupWizard.value.error = error.data.non_field_errors[0];
      }
      throw error;
    }
  });
}
async function setupWizardSetName() {
  await requestWrapper(async () => {
    const obj = await $fetch<MfaMethod>(`/api/v1/pentestusers/self/mfa/${setupWizard.value.newMfaMethod!.id}/`, {
      method: 'PATCH',
      body: {
        name: setupWizard.value.newMfaMethod!.name,
      },
    });
    mfaMethods.value = [obj].concat(mfaMethods.value);
    setupWizard.value.visible = false;
    successToast('MFA setup completed');
  });
}

function openEditWizard(mfaMethod: MfaMethod) {
  editWizard.value = {
    visible: true,
    methodType: mfaMethodChoices.find(c => c.value === mfaMethod.method_type)!,
    form: cloneDeep(mfaMethod),
  };
}
async function editWizardSave() {
  await requestWrapper(async () => {
    await $fetch(`/api/v1/pentestusers/self/mfa/${editWizard.value.form!.id}/`, {
      method: 'PATCH',
      body: editWizard.value.form!,
    });
    mfaMethods.value = await $fetch(`/api/v1/pentestusers/self/mfa/`, { method: 'GET' });
    editWizard.value.visible = false;
  });
}

async function deleteMfaMethod(mfaMethod: MfaMethod) {
  await requestWrapper(async () => {
    await $fetch(`/api/v1/pentestusers/self/mfa/${mfaMethod.id}/`, {
      method: 'DELETE',
    });
    mfaMethods.value = mfaMethods.value.filter(m => m.id !== mfaMethod.id);
  });
}

const fromChangePassword = ref<VForm|null>(null);
async function changePassword() {
  if (!(await fromChangePassword.value!.validate()).valid) {
    return;
  }

  await requestWrapper(async () => {
    try {
      changePasswordWizard.value.errors = null;
      await $fetch('/api/v1/pentestusers/self/change-password/', {
        method: 'POST',
        body: {
          password: changePasswordWizard.value.password,
        },
      });
      changePasswordWizard.value.visible = false;
      changePasswordWizard.value.password = '';
      successToast('Password changed');
    } catch (error: any) {
      if (error?.status === 400 && error?.data?.password) {
        changePasswordWizard.value.errors = error?.data;
      }
    }
  });
}

</script>

<style lang="scss" scoped>
.backup-code-list {
  list-style: none;
  columns: 2;
  font-family: monospace;
}

.totp-confirm {
  max-width: 30em;
}
</style>
