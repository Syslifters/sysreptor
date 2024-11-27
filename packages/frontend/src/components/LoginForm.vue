<template>
  <s-card>
    <v-toolbar color="header" flat>
      <v-toolbar-title>
        <slot name="title">
          <template v-if="step === LoginStep.CHANGE_PASSWORD">Change Password</template>
          <template v-else>Login</template>
        </slot>
      </v-toolbar-title>
    </v-toolbar>

    <template v-if="step === LoginStep.USERNAME">
      <v-form ref="form" @submit.prevent="loginUsername">
        <v-card-text>
          <v-text-field
            v-model="formUsername.username"
            type="text"
            name="username"
            label="Username"
            prepend-icon="mdi-account"
            spellcheck="false"
            autocomplete="off"
            :autofocus="!username"
            :disabled="Boolean(username)"
            required
          />
          <v-text-field
            v-model="formUsername.password"
            type="password"
            name="password"
            label="Password"
            prepend-icon="mdi-lock"
            class="mt-4"
            :autofocus="Boolean(username)"
            required
          />

          <slot name="message" />
          <p v-if="errorMessage" class="text-error">
            {{ errorMessage }}
          </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <slot name="actions"></slot>
          <s-btn-primary
            type="submit"
            text="Login"
          />
        </v-card-actions>
      </v-form>
    </template>

    <template v-else-if="step === LoginStep.MFA">
      <v-form ref="form" @submit.prevent="loginCode">
        <v-card-text>
          <v-card-title>
            <v-icon start :icon="mfaMethodChoices.find(c => c.value === currentMfaMethod!.method_type)?.icon" />
            {{ currentMfaMethod!.name }}
          </v-card-title>

          <template v-if="currentMfaMethod!.method_type === MfaMethodType.FIDO2">
            <p>Use your security key to log in.</p>
          </template>
          <template v-else-if="currentMfaMethod!.method_type === MfaMethodType.TOTP">
            <v-otp-input
              ref="otpRef"
              v-model="formCode.code"
              type="number"
              length="6"
              @finish="loginCode"
              spellcheck="false"
              autocomplete="off"
              autofocus
              required
            />
          </template>
          <template v-else-if="currentMfaMethod!.method_type === MfaMethodType.BACKUP">
            <v-otp-input
              ref="otpRef"
              v-model="formCode.code"
              type="text"
              length="12"
              @finish="loginCode"
              spellcheck="false"
              autocomplete="off"
              autofocus
              required
            />
          </template>

          <slot name="message" />
          <p v-if="errorMessage" class="text-error">
            {{ errorMessage }}
          </p>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <s-btn-other
            v-if="mfaMethods!.length > 1"
            @click="step = LoginStep.MFA_SELECT"
            text="Try another MFA method"
          />
          <s-btn-primary
            v-if="[MfaMethodType.TOTP, MfaMethodType.BACKUP].includes(currentMfaMethod!.method_type as any)"
            type="submit"
            text="Login"
          />
          <s-btn-primary
            v-else-if="currentMfaMethod?.method_type === MfaMethodType.FIDO2"
            @click="beginMfaLogin(currentMfaMethod)"
            text="Try again"
          />
        </v-card-actions>
      </v-form>
    </template>

    <template v-else-if="step === LoginStep.MFA_SELECT">
      <v-card-text>
        <h2>Choose MFA method</h2>

        <v-list>
          <v-list-item v-for="mfaMethod in mfaMethods" :key="mfaMethod.id" link @click="beginMfaLogin(mfaMethod)">
            <v-list-item-title>
              <v-icon start :icon="mfaMethodChoices.find(c => c.value === mfaMethod.method_type)?.icon" />
              {{ mfaMethod.name }}
            </v-list-item-title>
          </v-list-item>
        </v-list>
      </v-card-text>
    </template>

    <template v-else-if="step === LoginStep.CHANGE_PASSWORD">
      <v-form ref="form" @submit.prevent="changePassword">
        <v-card-text>
          <s-password-field
            v-model="formChangePassword.password"
            confirm show-strength
            label="New Password"
          />

          <p v-if="errorMessage" class="text-error">
            {{ errorMessage }}
          </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <s-btn-primary
            type="submit"
            text="Change Password"
          />
        </v-card-actions>
      </v-form>
    </template>
  </s-card>
</template>

<script setup lang="ts">
import { get as navigatorCredentialsGet, parseRequestOptionsFromJSON } from "@github/webauthn-json/browser-ponyfill";
import type { VOtpInput } from "vuetify/components";
import { LoginResponseStatus, mfaMethodChoices, MfaMethodType } from '#imports';

const props = defineProps({
  username: {
    type: String,
    default: null
  },
});
const emit = defineEmits(['login']);
const auth = useAuth();

enum LoginStep {
  USERNAME = 'username',
  MFA = 'mfa',
  MFA_SELECT = 'mfa-select',
  CHANGE_PASSWORD = 'change-password',
}

const step = ref<LoginStep>(LoginStep.USERNAME);
const actionInProgress = ref(false);
const errorMessage = ref<string | null>(null);
const formUsername = ref({
  username: props.username || '',
  password: '',
})
const mfaMethods = ref<MfaMethod[] | null>(null);
const currentMfaMethod = ref<MfaMethod | null>(null);
const formCode = ref({
  code: '',
});
const otpRef = ref<VOtpInput|null>(null);
const formChangePassword = ref({
  password: '',
});

async function loginStep(fn: () => Promise<LoginResponse|null>) {
  if (actionInProgress.value) {
    return;
  }

  try {
    actionInProgress.value = true;
    errorMessage.value = null;

    const res = await fn();
    if (!res) {
      return;
    }

    if (res.status === LoginResponseStatus.SUCCESS) {
      // trigger login in nuxt-auth
      await auth.fetchUser();
      emit('login', res);
    } else if (res.status === LoginResponseStatus.MFA_REQUIRED) {
      mfaMethods.value = res.mfa!;
      beginMfaLogin(mfaMethods.value!.find(m => m.is_primary) || mfaMethods.value![0]!)
    } else if (res.status === LoginResponseStatus.PASSWORD_CHANGE_REQUIRED) {
      step.value = LoginStep.CHANGE_PASSWORD;
    }
  } catch (error: any) {
    if (error?.data?.detail) {
      errorMessage.value = error.data.detail;
    } else if (error?.data?.non_field_errors) {
      errorMessage.value = error.data.non_field_errors[0];
    } else if (error?.data?.password) {
      errorMessage.value = error.data.password.join(', ');
    } else if (error instanceof DOMException) {
      errorMessage.value = error.message;
    } else {
      requestErrorToast({ error, message: 'Login failed' });
    }
  } finally {
    actionInProgress.value = false;
  }
}

async function loginUsername() {
  await loginStep(async () => {
    if (!formUsername.value.username || !formUsername.value.password) {
      errorMessage.value = 'Username and password are required';
      return null;
    }
    return await $fetch('/api/v1/auth/login/', { method: 'POST', body: formUsername.value });
  });
}

async function beginMfaLogin(mfaMethod: MfaMethod) {
  currentMfaMethod.value = mfaMethod;
  step.value = LoginStep.MFA;
  errorMessage.value = null;
  formCode.value = { code: '' };

  if (currentMfaMethod.value.method_type === MfaMethodType.FIDO2) {
    // Start FIDO2 flow
    await nextTick();
    await loginStep(async () => {
      const options = await $fetch<any>('/api/v1/auth/login/fido2/begin/', { method: 'POST', body: {} });
      const fido2Response = await navigatorCredentialsGet(parseRequestOptionsFromJSON(options));
      return await $fetch('/api/v1/auth/login/fido2/complete/', { method: 'POST', body: fido2Response });
    });
  } else {
    // Autofocus OTP input
    await nextTick();
    otpRef.value?.focus();
  }
}

async function loginCode() {
  await loginStep(async () => {
    return await $fetch('/api/v1/auth/login/code/', {
      method: 'POST',
      body: {
        id: currentMfaMethod.value!.id,
        code: formCode.value.code,
      },
    });
  });
}

async function changePassword() {
  await loginStep(async () => {
    return await $fetch('/api/v1/auth/login/change-password/', {
      method: 'POST',
      body: {
        password: formChangePassword.value.password,
      },
    });
  })
}

</script>
