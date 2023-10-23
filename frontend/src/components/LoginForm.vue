<template>
  <s-card>
    <v-toolbar class="login-header" theme="dark" flat>
      <v-toolbar-title><slot name="title">Login</slot></v-toolbar-title>
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
          <s-btn
            type="submit"
            text="Login"
            color="primary"
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
          <s-btn
            v-if="mfaMethods!.length > 1"
            @click="step = LoginStep.MFA_SELECT"
            text="Try another MFA method"
          />
          <s-btn
            v-if="[MfaMethodType.TOTP, MfaMethodType.BACKUP].includes(currentMfaMethod!.method_type as any)"
            type="submit"
            text="Login"
            color="primary"
          />
          <s-btn
            v-else-if="currentMfaMethod?.method_type === MfaMethodType.FIDO2"
            @click="beginMfaLogin(currentMfaMethod)"
            text="Try again"
            color="primary"
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
  </s-card>
</template>

<script setup lang="ts">
import { get as navigatorCredentialsGet, parseRequestOptionsFromJSON } from "@github/webauthn-json/browser-ponyfill";
import { LoginResponse, LoginResponseStatus, MfaMethod, mfaMethodChoices, MfaMethodType } from '@/utils/types';

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
      beginMfaLogin(mfaMethods.value!.find(m => m.is_primary) || mfaMethods.value![0])
    }
  } catch (error: any) {
    if (error?.data?.detail) {
      errorMessage.value = error.data.detail;
    } else if (error?.data?.non_field_errors) {
      errorMessage.value = error.data.non_field_errors[0];
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
    await nextTick();
    await loginStep(async () => {
      const options = await $fetch<any>('/api/v1/auth/login/fido2/begin/', { method: 'POST', body: {} });
      const fido2Response = await navigatorCredentialsGet(parseRequestOptionsFromJSON(options));
      return await $fetch('/api/v1/auth/login/fido2/complete/', { method: 'POST', body: fido2Response });
    });
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

</script>
